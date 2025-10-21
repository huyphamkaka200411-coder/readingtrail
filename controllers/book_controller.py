"""
Book Controller
Handles book-related operations like browsing, borrowing, posting, and management.
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from config import db
from models import Book, BorrowedBook, User, Notification
from datetime import datetime, timedelta
import logging

def index():
    """Home page with book catalog"""
    from models.book import BorrowedBook

    books = load_books()
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    location_filter = request.args.get('location', '').strip()  # ✅ thêm lọc vị trí

    # ✅ Lọc theo từ khóa
    if search_query:
        books = [
            book for book in books
            if search_query.lower() in book.title.lower()
            or search_query.lower() in book.author.lower()
            or (book.description and search_query.lower() in book.description.lower())
        ]

    # ✅ Lọc theo thể loại
    if category_filter:
        books = [book for book in books if category_filter.lower() in book.category.lower()]

    # ✅ Lọc theo vị trí
    if location_filter:
        books = [book for book in books if location_filter.lower() in book.location.lower()]

    # ✅ Lấy danh sách thể loại và vị trí duy nhất để hiển thị gợi ý hoặc dropdown
    all_books = load_books()
    categories = sorted(list(set(book.category for book in all_books if book.category)))
    locations = sorted(list(set(book.location for book in all_books if book.location)))

    # ✅ Lấy các yêu cầu mượn đang chờ duyệt
    pending_requests = []
    if current_user.is_authenticated:
        pending_requests = BorrowedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False,
            is_agreed=False
        ).all()
        pending_requests = [req.book_id for req in pending_requests]

    return render_template(
        'index.html',
        books=books,
        search_query=search_query,
        category_filter=category_filter,
        location_filter=location_filter,  # ✅ truyền vào template
        categories=categories,
        locations=locations,
        pending_requests=pending_requests
    )



def book_detail(book_id):
    """Book detail page"""
    book = get_book_by_id(book_id)
    if not book:
        return render_template('404.html'), 404

    # Check if user has borrowed this book
    is_borrowed = False
    borrow_request = None

    if current_user.is_authenticated:
        borrowed_books = get_borrowed_books()
        is_borrowed = book_id in borrowed_books

        # Check for pending borrow request
        borrow_request = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False
        ).first()

    return render_template('book_detail.html', 
                         book=book, 
                         is_borrowed=is_borrowed,
                         borrow_request=borrow_request)


def borrow_book(book_id):
    """Request to borrow a book"""
    from models.book import BorrowedBook

    if not current_user.is_authenticated:
        flash('Please login to borrow books', 'error')
        return redirect(url_for('login'))

    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found', 'error')
        return redirect(url_for('index'))

    # Check if user is trying to borrow their own book
    if book.poster and book.poster.id == current_user.id:
        flash('You cannot borrow your own book', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    # Check if book is available
    if not book.available:
        flash('This book is not available for borrowing', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    # Check if user has already borrowed this book
    existing_borrow = BorrowedBook.query.filter_by(
        book_id=book_id,
        user_id=current_user.id,
        is_returned=False
    ).first()

    if existing_borrow:
        flash('You have already borrowed this book or have a pending request', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    # Get proposed due date from form
    proposed_due_date = request.form.get('proposed_due_date')
    if proposed_due_date:
        try:
            proposed_due_date = datetime.strptime(proposed_due_date, '%Y-%m-%d')
        except ValueError:
            proposed_due_date = None

    # Create borrow request
    try:
        create_borrow_request(book_id, proposed_due_date)

        # Check borrow status for template
        is_borrowed = False
        borrow_request = None

        if current_user.is_authenticated:
            borrowed_books = get_borrowed_books()
            is_borrowed = book_id in borrowed_books

            # Check for pending borrow request
            from models.book import BorrowedBook
            borrow_request = BorrowedBook.query.filter_by(
                book_id=book_id,
                user_id=current_user.id,
                is_returned=False
            ).first()

        # Prepare success data for modal
        success_data = {
            'show_borrow_success_modal': True,
            'book_title': book.title,
            'poster_name': book.poster.get_full_name() if book.poster else 'Book Owner',
            'is_borrowed': is_borrowed,
            'borrow_request': borrow_request
        }

        return render_template('book_detail.html', book=book, **success_data)
    except Exception as e:
        logging.error(f"Error creating borrow request: {e}")
        flash('Failed to create borrow request', 'error')

    return redirect(url_for('book_detail', book_id=book_id))


def return_book(book_id):
    """Return a borrowed book"""
    if not current_user.is_authenticated:
        flash('Please login to return books', 'error')
        return redirect(url_for('login'))

    try:
        remove_borrowed_book(book_id)
        flash('Book returned successfully!', 'success')
    except Exception as e:
        logging.error(f"Error returning book: {e}")
        flash('Failed to return book', 'error')

    return redirect(url_for('dashboard'))


def post_book():
    """Add a new book to the catalog (now includes borrow duration in weeks, location, and cover image)"""
    if not current_user.is_authenticated:
        flash('Please login to post books', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        cover_url = request.form.get('cover_url', '').strip()  # ✅ Thêm dòng này
        publication_year = request.form.get('publication_year')
        pages = request.form.get('pages')
        borrow_duration_weeks = request.form.get('borrow_duration_weeks', '2').strip()

        # ✅ Kiểm tra trường bắt buộc
        if not title or not author or not category or not location:
            flash('Vui lòng điền đầy đủ các trường bắt buộc (Tên, Tác giả, Thể loại, Vị trí).', 'error')
            return render_template('post_book.html')

        # ✅ Tạo sách mới (có ảnh bìa)
        book = Book(
            title=title,
            author=author,
            category=category,
            location=location,
            description=description,
            cover_url=cover_url,   # ✅ thêm dòng này
            publication_year=int(publication_year) if publication_year else None,
            pages=int(pages) if pages else None,
            posted_by=current_user.id,
            borrow_duration_weeks=int(borrow_duration_weeks) if borrow_duration_weeks.isdigit() else 2
        )

        try:
            db.session.add(book)
            db.session.commit()
            flash('Đăng sách thành công!', 'success')
            return render_template('post_book.html', show_success_modal=True, book_title=title)
        except Exception as e:
            db.session.rollback()
            logging.error(f"Lỗi đăng sách: {e}")
            flash('Không thể đăng sách. Vui lòng thử lại.', 'error')

    return render_template('post_book.html')



def update_book_status(book_id):
    """Toggle book availability status (available/unavailable)"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401

    try:
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({'success': False, 'message': 'Không tìm thấy sách'}), 404

        # Check if current user is the book owner
        if book.posted_by != current_user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật sách này'}), 403

        # Toggle availability
        book.available = not book.available
        db.session.commit()

        status_text = "có sẵn để cho mượn" if book.available else "không còn cho mượn"
        return jsonify({
            'success': True, 
            'message': f'Đã cập nhật trạng thái sách thành "{status_text}"',
            'available': book.available
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating book status: {e}")
        return jsonify({'success': False, 'message': 'Lỗi khi cập nhật trạng thái sách'}), 500


def delete_book(book_id):
    """Delete a book"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401

    try:
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({'success': False, 'message': 'Không tìm thấy sách'}), 404

        # Check if current user is the book owner
        if book.posted_by != current_user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền xóa sách này'}), 403

        # Check if book is currently borrowed
        active_borrows = BorrowedBook.query.filter_by(
            book_id=book_id,
            is_returned=False
        ).count()

        if active_borrows > 0:
            return jsonify({
                'success': False, 
                'message': 'Không thể xóa sách đang được mượn. Vui lòng đợi người mượn trả sách trước.'
            }), 400

        book_title = book.title
        db.session.delete(book)
        db.session.commit()

        return jsonify({
            'success': True, 
            'message': f'Đã xóa sách "{book_title}" thành công'
        })

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting book: {e}")
        return jsonify({'success': False, 'message': 'Lỗi khi xóa sách'}), 500


def dashboard():
    """User dashboard with borrowed books and posted books"""
    if not current_user.is_authenticated:
        flash('Please login to view your dashboard', 'error')
        return redirect(url_for('login'))

    # Get borrowed books
    borrowed_books = get_borrowed_books()
    borrowed_book_objects = []

    for book_id in borrowed_books:
        book = get_book_by_id(book_id)
        if book:
            borrow_record = BorrowedBook.query.filter_by(
                book_id=book_id,
                user_id=current_user.id,
                is_returned=False
            ).first()

            if borrow_record:
                # Add borrow record info to book object
                book.due_date = borrow_record.due_date.strftime('%d/%m/%Y') if borrow_record.due_date else None
                book.is_overdue = borrow_record.due_date < datetime.now() if borrow_record.due_date else False
                borrowed_book_objects.append(book)

    # Get books posted by current user
    posted_books = Book.query.filter_by(posted_by=current_user.id).all()

    # Get pending borrow requests
    pending_requests = get_pending_borrow_requests()

    return render_template('dashboard.html', 
                         borrowed_books=borrowed_book_objects,
                         posted_books=posted_books,
                         pending_requests=pending_requests)


def seed_books():
    """Seed the database with sample books"""
    try:
        # Check if books already exist
        if Book.query.count() > 0:
            return "Books already exist in the database"

        sample_books = [
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'category': 'Fiction',
                'isbn': '978-0-06-112008-4',
                'description': 'A gripping tale of racial injustice and childhood innocence in the American South.',
                'publication_year': 1960,
                'pages': 281,
                'borrow_duration_weeks': 2
            },
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'category': 'Fiction',
                'isbn': '978-0-7432-7356-5',
                'description': 'A classic American novel about the Jazz Age and the American Dream.',
                'publication_year': 1925,
                'pages': 180,
                'borrow_duration_weeks': 3
            }
        ]

        for book_data in sample_books:
            book = Book(**book_data)
            db.session.add(book)

        db.session.commit()
        logging.info("Sample books seeded successfully")
        return "Sample books added successfully!"

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding books: {e}")
        return f"Error seeding books: {e}"


# Helper functions
def load_books():
    """Load books from database"""
    try:
        books = Book.query.order_by(Book.created_at.desc()).all()
        for book in books:
            if book.posted_by:
                poster = User.query.get(book.posted_by)
        return books
    except Exception as e:
        logging.error(f"Error loading books: {e}")
        return []


def get_book_by_id(book_id):
    """Get a specific book by ID from database"""
    try:
        return Book.query.get(book_id)
    except Exception as e:
        logging.error(f"Error getting book {book_id}: {e}")
        return None


def get_borrowed_books():
    """Get list of borrowed book IDs for current user (only approved borrowings)"""
    if not current_user.is_authenticated:
        return []

    try:
        borrowed_records = BorrowedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False,
            is_agreed=True
        ).all()
        return [record.book_id for record in borrowed_records]
    except Exception as e:
        logging.error(f"Error getting borrowed books: {e}")
        return []


def get_pending_borrow_requests():
    """Get pending borrow requests for current user"""
    if not current_user.is_authenticated:
        return []

    try:
        pending_requests = BorrowedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False,
            is_agreed=False
        ).all()

        requests_with_books = []
        for request in pending_requests:
            book = get_book_by_id(request.book_id)
            if book:
                requests_with_books.append({
                    'request': request,
                    'book': book
                })

        return requests_with_books
    except Exception as e:
        logging.error(f"Error getting pending requests: {e}")
        return []


def create_borrow_request(book_id, proposed_due_date=None):
    """Create a borrow request (pending approval)"""
    if not current_user.is_authenticated:
        raise Exception("User must be logged in")

    from models.book import BorrowedBook
    from config import db

    book = get_book_by_id(book_id)
    weeks = book.borrow_duration_weeks if book and book.borrow_duration_weeks else 2

    if not proposed_due_date:
        proposed_due_date = datetime.utcnow() + timedelta(weeks=weeks)

    borrow_record = BorrowedBook(
        book_id=book_id,
        user_id=current_user.id,
        due_date=proposed_due_date,
        is_agreed=False
    )

    db.session.add(borrow_record)
    db.session.commit()

    # Create notification for book owner
    if book and book.posted_by:
        create_borrow_notification(book, current_user.get_full_name() or current_user.username, proposed_due_date)

    logging.info(f"Borrow request created for book {book_id} by user {current_user.id}")


def create_borrow_notification(book, borrower_name, proposed_due_date=None):
    """Create a notification when someone borrows a user-posted book"""
    if not book.posted_by:
        return

    from models.social import Notification
    from config import db

    due_date_str = proposed_due_date.strftime('%Y-%m-%d') if proposed_due_date else 'Not specified'

    notification = Notification(
        user_id=book.posted_by,
        book_id=book.id,
        type='borrow_request',
        title='New Borrow Request',
        message=f'{borrower_name} wants to borrow "{book.title}" (due: {due_date_str})',
        related_user_id=current_user.id
    )

    db.session.add(notification)
    db.session.commit()

    logging.info(f"Notification created for user {book.posted_by} about book {book.id}")


def remove_borrowed_book(book_id):
    """Return a borrowed book in database"""
    if not current_user.is_authenticated:
        raise Exception("User must be logged in")

    borrow_record = BorrowedBook.query.filter_by(
        book_id=book_id,
        user_id=current_user.id,
        is_returned=False
    ).first()

    if not borrow_record:
        raise Exception("Book not found in borrowed list")

    borrow_record.is_returned = True
    borrow_record.returned_date = datetime.utcnow()

    book = get_book_by_id(book_id)
    if book:
        book.available = True

    db.session.commit()

    logging.info(f"Book {book_id} returned by user {current_user.id}")