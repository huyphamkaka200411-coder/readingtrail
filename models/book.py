from datetime import datetime
from config import db

class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(500))
    publication_year = db.Column(db.Integer)
    pages = db.Column(db.Integer)
    available = db.Column(db.Boolean, default=True)
    borrow_duration_weeks = db.Column(db.Integer, default=2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ CHỈ GIỮ LẠI DÒNG NÀY THÔI
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    poster = db.relationship('User', backref=db.backref('posted_books', lazy=True))

    def __repr__(self):
        return f'<Book {self.title}>'


    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'location': self.location,
            'description': self.description,
            'cover_url': self.cover_url,
            'publication_year': self.publication_year,
            'pages': self.pages,
            'available': self.available,
            'borrow_duration_weeks': self.borrow_duration_weeks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'posted_by': self.posted_by,
            'poster_name': self.poster.get_full_name() if self.poster else None
        }


    def get_average_rating(self):
        """Tính trung bình số sao của sách"""
        from models.review import BookReview
        reviews = BookReview.query.filter_by(book_id=self.id).all()
        if not reviews:
            return 0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    def get_review_count(self):
        """Đếm tổng số lượt đánh giá"""
        from models.review import BookReview
        return BookReview.query.filter_by(book_id=self.id).count()


class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100))  # Cho người mượn không đăng nhập
    borrowed_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    agreed_due_date = db.Column(db.DateTime)  # Ngày trả được thống nhất
    returned_date = db.Column(db.DateTime)
    is_returned = db.Column(db.Boolean, default=False)
    is_agreed = db.Column(db.Boolean, default=False)  # Người đăng đồng ý cho mượn hay chưa

    def __repr__(self):
        return f'<BorrowedBook {self.book_id} by {self.user_id}>'

    def is_overdue(self):
        """Kiểm tra xem sách có bị quá hạn hay không"""
        due_date = self.agreed_due_date if self.agreed_due_date else self.due_date
        return datetime.utcnow() > due_date and not self.is_returned

    def to_dict(self):
        """Trả về dữ liệu ở dạng dictionary"""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'borrowed_date': self.borrowed_date.isoformat() if self.borrowed_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'agreed_due_date': self.agreed_due_date.isoformat() if self.agreed_due_date else None,
            'returned_date': self.returned_date.isoformat() if self.returned_date else None,
            'is_returned': self.is_returned,
            'is_agreed': self.is_agreed,
            'is_overdue': self.is_overdue()
        }
