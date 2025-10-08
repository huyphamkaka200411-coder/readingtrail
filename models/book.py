from datetime import datetime
from config import db


class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(500))
    publication_year = db.Column(db.Integer)
    pages = db.Column(db.Integer)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    borrowed_records = db.relationship('BorrowedBook', backref='book', lazy=True, cascade='all, delete-orphan')
    poster = db.relationship('User', backref=db.backref('posted_books', lazy=True))
    
    def __repr__(self):
        return f'<Book {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'isbn': self.isbn,
            'description': self.description,
            'cover_url': self.cover_url,
            'publication_year': self.publication_year,
            'pages': self.pages,
            'available': self.available,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'posted_by': self.posted_by
        }
    
    def get_average_rating(self):
        """Calculate average rating for this book"""
        from models.review import BookReview
        reviews = BookReview.query.filter_by(book_id=self.id).all()
        if not reviews:
            return 0
        return sum(review.rating for review in reviews) / len(reviews)
    
    def get_review_count(self):
        """Get total number of reviews for this book"""
        from models.review import BookReview
        return BookReview.query.filter_by(book_id=self.id).count()


class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100))  # Optional for guest users
    borrowed_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    agreed_due_date = db.Column(db.DateTime)  # Negotiated due date between borrower and lender
    returned_date = db.Column(db.DateTime)
    is_returned = db.Column(db.Boolean, default=False)
    is_agreed = db.Column(db.Boolean, default=False)  # Whether lender has agreed to the terms
    
    def __repr__(self):
        return f'<BorrowedBook {self.book_id} by {self.user_id}>'
    
    def is_overdue(self):
        """Check if the book is overdue"""
        due_date = self.agreed_due_date if self.agreed_due_date else self.due_date
        return datetime.utcnow() > due_date and not self.is_returned
    
    def to_dict(self):
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