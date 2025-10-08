import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Import models and initialize database
from models import db, Book, BorrowedBook, User, Discussion, Notification, PrivateMessage, BookReview, UserProfile
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

@app.context_processor
def inject_borrowed_count():
    """Inject borrowed count and notification count into all templates"""
    try:
        borrowed_count = len(get_borrowed_books())
        
        # Get notification count for current user
        if current_user.is_authenticated:
            notification_count = Notification.query.filter_by(
                recipient_user_id=current_user.id,
                is_read=False
            ).count()
        else:
            session_id = session.get('session_id')
            if session_id:
                notification_count = Notification.query.filter_by(
                    recipient_session_id=session_id,
                    is_read=False
                ).count()
            else:
                notification_count = 0
        
        return {
            'borrowed_count': borrowed_count,
            'notification_count': notification_count
        }
    except Exception as e:
        logging.error(f"Error in context processor: {e}")
        return {'borrowed_count': 0, 'notification_count': 0}

def get_user_identifier():
    """Get user ID if logged in, otherwise session ID"""
    if current_user.is_authenticated:
        return current_user.id
    else:
        if 'session_id' not in session:
            import uuid
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']

def load_books():
    """Load books from database"""
    try:
        books = Book.query.all()
        book_list = []
        for book in books:
            book_dict = book.to_dict()
            # Add poster information
            if book.posted_by:
                poster = User.query.get(book.posted_by)
                if poster:
                    book_dict['poster'] = {
                        'id': poster.id,
                        'username': poster.username,
                        'full_name': poster.get_full_name()
                    }
            book_list.append(book_dict)
        return book_list
    except Exception as e:
        logging.error(f"Error loading books from database: {e}")
        return []

def get_book_by_id(book_id):
    """Get a specific book by ID from database"""
    try:
        book = Book.query.get(book_id)
        if book:
            book_dict = book.to_dict()
            # Add poster information
            if book.posted_by:
                poster = User.query.get(book.posted_by)
                if poster:
                    book_dict['poster'] = {
                        'id': poster.id,
                        'username': poster.username,
                        'full_name': poster.get_full_name()
                    }
                    logging.info(f"Added poster info for book {book_id}: {book_dict['poster']}")
                else:
                    logging.warning(f"Poster user {book.posted_by} not found for book {book_id}")
            else:
                logging.info(f"No posted_by field for book {book_id}")
            return book_dict
        return None
    except Exception as e:
        logging.error(f"Error getting book {book_id}: {e}")
        return None

def get_borrowed_books():
    """Get list of borrowed book IDs for current user (only approved borrowings)"""
    try:
        if current_user.is_authenticated:
            borrowed_books = BorrowedBook.query.filter_by(
                user_id=current_user.id,
                is_returned=False,
                is_agreed=True  # Only include approved borrowings
            ).all()
            return [bb.book_id for bb in borrowed_books]
        else:
            # No borrowing for guest users
            return []
    except Exception as e:
        logging.error(f"Error getting borrowed books: {e}")
        return []


def get_pending_borrow_requests():
    """Get pending borrow requests for current user"""
    try:
        if current_user.is_authenticated:
            pending_requests = BorrowedBook.query.filter_by(
                user_id=current_user.id,
                is_returned=False,
                is_agreed=False  # Only pending requests
            ).all()
            
            # Get book details for each request
            requests_with_books = []
            for request in pending_requests:
                book = get_book_by_id(request.book_id)
                if book:
                    requests_with_books.append({
                        'request': request,
                        'book': book
                    })
            
            return requests_with_books
        else:
            return []
    except Exception as e:
        logging.error(f"Error getting pending requests: {e}")
        return []

def add_borrowed_book(book_id, proposed_due_date=None):
    """Add a book to the borrowed books list in database"""
    try:
        # Only authenticated users can borrow books
        if not current_user.is_authenticated:
            return False
            
        # Get the book details
        book = Book.query.get(book_id)
        if not book:
            return False
            
        # Check if already borrowed by this user
        existing = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False
        ).first()
        
        if not existing:
            # Default due date if none proposed
            default_due_date = datetime.utcnow() + timedelta(weeks=2)
            
            # Parse proposed due date
            agreed_due_date = None
            if proposed_due_date:
                try:
                    agreed_due_date = datetime.fromisoformat(proposed_due_date.replace('Z', '+00:00'))
                except:
                    agreed_due_date = None
            
            borrowed_book = BorrowedBook()
            borrowed_book.book_id = book_id
            borrowed_book.user_id = current_user.id
            borrowed_book.due_date = default_due_date
            borrowed_book.agreed_due_date = agreed_due_date
            
            # For user-posted books, require approval. For system books, auto-approve
            if book.get('poster'):
                borrowed_book.is_agreed = False  # Needs lender approval
            else:
                borrowed_book.is_agreed = True  # Auto-approve for system books
                
            db.session.add(borrowed_book)
            
            # Create notification for borrow request
            create_borrow_notification(book, current_user.get_full_name() or current_user.username, agreed_due_date)
            
            db.session.commit()
            return True
        return False
    except Exception as e:
        logging.error(f"Error adding borrowed book {book_id}: {e}")
        db.session.rollback()
        return False

def create_borrow_request(book_id, proposed_due_date=None):
    """Create a borrow request (pending approval)"""
    from models import BorrowedBook, Book
    
    try:
        book = Book.query.get(book_id)
        if not book:
            logging.error(f"Book {book_id} not found")
            return False
        
        # Set default due date if not provided (2 weeks from now)
        if proposed_due_date:
            if isinstance(proposed_due_date, str):
                due_date = datetime.strptime(proposed_due_date, '%Y-%m-%d')
            else:
                due_date = proposed_due_date
        else:
            due_date = datetime.utcnow() + timedelta(weeks=2)
        
        # Create borrow request (not yet agreed)
        borrow_request = BorrowedBook()
        borrow_request.book_id = book_id
        borrow_request.user_id = current_user.id
        borrow_request.due_date = due_date
        borrow_request.agreed_due_date = due_date
        borrow_request.is_agreed = False  # Waiting for approval
        
        db.session.add(borrow_request)
        
        # Create notification for book owner
        create_borrow_notification(book, current_user.get_full_name(), due_date)
        
        db.session.commit()
        
        logging.info(f"Created borrow request for book {book_id} by user {current_user.id}")
        return True
        
    except Exception as e:
        logging.error(f"Error creating borrow request: {e}")
        db.session.rollback()
        return False


def create_borrow_notification(book, borrower_name, proposed_due_date=None):
    """Create a notification when someone borrows a user-posted book"""
    try:
        # Only create notification if the book has an owner (posted_by is set)
        if book.posted_by:
            notification = Notification()
            notification.book_id = book.id
            notification.recipient_user_id = book.posted_by  # Send to book owner
            notification.borrower_name = borrower_name
            
            # Include due date info in message
            due_date_text = ""
            if proposed_due_date:
                due_date_str = proposed_due_date.strftime('%B %d, %Y')
                due_date_text = f" with proposed return date: {due_date_str}"
            
            notification.message = f'{borrower_name} wants to borrow "{book.title}"{due_date_text}. Click to approve or negotiate.'
            notification.notification_type = 'borrow_request'
            
            db.session.add(notification)
            logging.info(f"Created borrow notification for book owner {book.posted_by} - book {book.title} requested by {borrower_name}")
        else:
            logging.info(f"No notification created for book {book.title} - no owner tracked")
    except Exception as e:
        logging.error(f"Error creating notification: {e}")

def remove_borrowed_book(book_id):
    """Return a borrowed book in database"""
    try:
        # Only authenticated users can return books
        if not current_user.is_authenticated:
            return False
            
        borrowed_book = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False
        ).first()
        
        if borrowed_book:
            borrowed_book.is_returned = True
            borrowed_book.returned_date = datetime.utcnow()
            db.session.commit()
            return True
        return False
    except Exception as e:
        logging.error(f"Error returning book {book_id}: {e}")
        db.session.rollback()
        return False

@app.route('/')
def index():
    """Home page with book catalog"""
    books = load_books()
    
    # Get search and filter parameters
    search_query = request.args.get('search', '').lower()
    category_filter = request.args.get('category', '')
    
    # Filter books based on search and category
    filtered_books = books
    
    if search_query:
        filtered_books = [
            book for book in filtered_books
            if search_query in book['title'].lower() or 
               search_query in book['author'].lower() or
               search_query in book.get('description', '').lower()
        ]
    
    if category_filter:
        filtered_books = [
            book for book in filtered_books
            if book['category'].lower() == category_filter.lower()
        ]
    
    # Get unique categories for filter dropdown
    categories = list(set(book['category'] for book in books))
    categories.sort()
    
    borrowed_books = get_borrowed_books()
    
    return render_template('index.html', 
                         books=filtered_books, 
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter,
                         borrowed_books=borrowed_books)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    """Book detail page"""
    book = get_book_by_id(book_id)
    if not book:
        return "Book not found", 404
    
    borrowed_books = get_borrowed_books()
    is_borrowed = book_id in borrowed_books
    
    return render_template('book_detail.html', 
                         book=book, 
                         is_borrowed=is_borrowed,
                         datetime=datetime,
                         timedelta=timedelta)

@app.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    """Request to borrow a book"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({
            'success': False, 
            'message': 'Please log in to borrow books. Real book borrowing requires an account.'
        }), 401
    
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': 'Book not found'}), 404
    
    # Check if user is trying to borrow their own book
    if book.get('posted_by') == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot borrow your own book'}), 400
    
    # Check if book is available
    if not book.get('available', True):
        return jsonify({'success': False, 'message': 'Book is currently unavailable'}), 400
    
    # Check if user already has a pending or approved borrow request for this book
    from models import BorrowedBook
    existing_request = BorrowedBook.query.filter_by(
        book_id=book_id, 
        user_id=current_user.id,
        is_returned=False
    ).first()
    
    if existing_request:
        if existing_request.is_agreed:
            return jsonify({'success': False, 'message': 'You already have this book borrowed'}), 400
        else:
            return jsonify({'success': False, 'message': 'You already have a pending request for this book'}), 400
    
    # Get proposed due date from request
    data = request.get_json() if request.is_json else {}
    proposed_due_date = data.get('proposed_due_date')
    
    # Create borrow request (not yet approved)
    success = create_borrow_request(book_id, proposed_due_date)
    
    if success:
        return jsonify({
            'success': True, 
            'message': f'Borrow request sent for "{book["title"]}". Waiting for owner approval.'
        })
    else:
        return jsonify({
            'success': False, 
            'message': 'Cannot borrow book. Please try again later.'
        }), 500

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    """Return a borrowed book"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        return jsonify({
            'success': False, 
            'message': 'Please log in to return books.'
        }), 401
    
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({'success': False, 'message': 'Book not found'}), 404
    
    borrowed_books = get_borrowed_books()
    if book_id not in borrowed_books:
        return jsonify({'success': False, 'message': 'Book not borrowed'}), 400
    
    remove_borrowed_book(book_id)
    
    # Check for new achievements
    new_achievements = check_and_award_achievements(current_user.id)
    
    return jsonify({
        'success': True, 
        'message': f'Successfully returned "{book["title"]}"',
        'new_achievements': [ach.to_dict() for ach in new_achievements] if new_achievements else []
    })

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with borrowed books"""
    try:
        # Get approved borrowed books
        approved_records = BorrowedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False,
            is_agreed=True
        ).all()
        
        borrowed_books = []
        for record in approved_records:
            book = Book.query.get(record.book_id)
            if book:
                book_dict = book.to_dict()
                book_dict['due_date'] = record.due_date.strftime('%B %d, %Y')
                book_dict['is_overdue'] = record.is_overdue
                borrowed_books.append(book_dict)
        
        # Get pending borrow requests
        pending_requests = get_pending_borrow_requests()
        
        return render_template('dashboard.html', 
                             borrowed_books=borrowed_books,
                             pending_requests=pending_requests)
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', borrowed_books=[], pending_requests=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember', False))
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/signup.html')
        
        if password and len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/signup.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/signup.html')
        
        # Create new user
        try:
            user = User()
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'danger')
    
    return render_template('auth/signup.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    user_name = current_user.get_full_name()
    logout_user()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/post-book', methods=['GET', 'POST'])
@login_required
def post_book():
    """Add a new book to the catalog"""
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title', '').strip()
            author = request.form.get('author', '').strip()
            category = request.form.get('category', '').strip()
            isbn = request.form.get('isbn', '').strip()
            description = request.form.get('description', '').strip()
            cover_url = request.form.get('cover_url', '').strip()
            publication_year = request.form.get('publication_year', '').strip()
            pages = request.form.get('pages', '').strip()
            price = request.form.get('price', '').strip()
            contact = request.form.get('contact', '').strip()
            
            # Validation
            if not all([title, author, category]):
                flash('Title, Author, and Category are required fields.', 'danger')
                return render_template('post_book.html')
            
            # Validate category selection
            valid_categories = [
                'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Science Fiction', 'Fantasy',
                'Biography', 'History', 'Self-Help', 'Business', 'Technology', 'Classic Literature',
                'Educational', 'Health & Fitness', 'Travel', 'Cooking', 'Art & Design',
                'Philosophy', 'Religion & Spirituality', 'Politics', 'Psychology', 'True Crime',
                'Horror', 'Thriller', 'Young Adult', 'Children\'s', 'Poetry', 'Drama',
                'Comics & Graphic Novels', 'Other'
            ]
            
            if category not in valid_categories:
                flash('Please select a valid category.', 'danger')
                return render_template('post_book.html')
            
            # Check if ISBN already exists
            if isbn and Book.query.filter_by(isbn=isbn).first():
                flash('A book with this ISBN already exists.', 'danger')
                return render_template('post_book.html')
            
            # Create new book
            book = Book()
            book.title = title
            book.author = author
            book.category = category
            book.isbn = isbn if isbn else f"NO-ISBN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            book.description = description
            book.cover_url = cover_url
            book.posted_by = current_user.id if current_user.is_authenticated else None
            
            # Convert numeric fields
            try:
                if publication_year:
                    book.publication_year = int(publication_year)
                if pages:
                    book.pages = int(pages)
            except ValueError:
                flash('Publication year and pages must be valid numbers.', 'danger')
                return render_template('post_book.html')
            
            # Add pricing and contact info to description
            extra_info = []
            if price:
                extra_info.append(f"Price: {price}")
            if contact:
                extra_info.append(f"Contact: {contact}")
            if extra_info:
                book.description = f"{book.description}\n\n{' | '.join(extra_info)}" if book.description else ' | '.join(extra_info)
            
            db.session.add(book)
            db.session.commit()
            
            flash(f'Book "{title}" has been successfully added to the catalog!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            logging.error(f"Error adding book: {e}")
            db.session.rollback()
            flash('An error occurred while adding the book. Please try again.', 'danger')
            return render_template('post_book.html')
    
    return render_template('post_book.html')

@app.route('/admin/add-book', methods=['POST'])
def add_book():
    """Add a new book to the catalog"""
    try:
        data = request.get_json()
        
        # Check if book with ISBN already exists
        existing_book = Book.query.filter_by(isbn=data['isbn']).first()
        if existing_book:
            return jsonify({'success': False, 'message': 'Book with this ISBN already exists'}), 400
        
        book = Book(
            title=data['title'],
            author=data['author'],
            category=data['category'],
            isbn=data['isbn'],
            description=data.get('description', ''),
            cover_url=data.get('cover_url', ''),
            publication_year=data.get('publication_year'),
            pages=data.get('pages'),
            posted_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(book)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Book "{book.title}" added successfully', 'book': book.to_dict()})
    except Exception as e:
        logging.error(f"Error adding book: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to add book'}), 500

@app.route('/admin/seed-books', methods=['POST'])
def seed_books():
    """Seed the database with sample books"""
    try:
        # Check if books already exist
        if Book.query.count() > 0:
            return jsonify({'success': False, 'message': 'Books already exist in the database'}), 400
        
        sample_books = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'category': 'Classic Literature',
                'isbn': '978-0-7432-7356-5',
                'description': 'A classic American novel set in the Jazz Age, exploring themes of wealth, love, and the American Dream through the eyes of narrator Nick Carraway.',
                'cover_url': 'https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg',
                'publication_year': 1925,
                'pages': 180
            },
            {
                'title': 'To Kill a Mockingbird',
                'author': 'Harper Lee',
                'category': 'Classic Literature',
                'isbn': '978-0-06-112008-4',
                'description': 'A gripping tale of racial injustice and childhood innocence in the American South, told through the eyes of Scout Finch.',
                'cover_url': 'https://covers.openlibrary.org/b/isbn/9780061120084-L.jpg',
                'publication_year': 1960,
                'pages': 376
            },
            {
                'title': '1984',
                'author': 'George Orwell',
                'category': 'Science Fiction',
                'isbn': '978-0-452-28423-4',
                'description': 'A dystopian social science fiction novel about totalitarian control and the struggle for truth and freedom.',
                'cover_url': 'https://covers.openlibrary.org/b/isbn/9780452284234-L.jpg',
                'publication_year': 1949,
                'pages': 328
            }
        ]
        
        for book_data in sample_books:
            book = Book(**book_data)
            db.session.add(book)
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Added {len(sample_books)} sample books to the catalog'})
    except Exception as e:
        logging.error(f"Error seeding books: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to seed books'}), 500

@app.route('/discussion', methods=['GET', 'POST'])
def discussion():
    """Discussion/chat page"""
    if request.method == 'POST':
        try:
            message = request.form.get('message', '').strip()
            if not message:
                flash('Please enter a message.', 'warning')
                return redirect(url_for('discussion'))
            
            # Get username
            if current_user.is_authenticated:
                username = current_user.get_full_name() or current_user.username
                user_id = current_user.id
                session_id = None
            else:
                username = request.form.get('username', '').strip()
                if not username:
                    flash('Please enter your name.', 'warning')
                    return redirect(url_for('discussion'))
                user_id = None
                session_id = get_user_identifier()
            
            # Create discussion entry
            discussion_entry = Discussion()
            discussion_entry.message = message
            discussion_entry.username = username
            discussion_entry.user_id = user_id
            discussion_entry.session_id = session_id
            discussion_entry.book_id = None  # General discussion
            
            db.session.add(discussion_entry)
            db.session.commit()
            
            return redirect(url_for('discussion'))
            
        except Exception as e:
            logging.error(f"Error adding discussion message: {e}")
            db.session.rollback()
            flash('Error posting message. Please try again.', 'danger')
    
    # Get all discussion messages
    try:
        messages = Discussion.query.order_by(Discussion.created_at.asc()).all()
        return render_template('discussion.html', messages=messages)
    except Exception as e:
        logging.error(f"Error loading discussion: {e}")
        return render_template('discussion.html', messages=[])

@app.route('/api/discussion/messages')
def get_discussion_messages():
    """API endpoint to get discussion messages for real-time updates"""
    try:
        messages = Discussion.query.order_by(Discussion.created_at.asc()).all()
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        logging.error(f"Error fetching discussion messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notifications')
def notifications():
    """Notifications page"""
    try:
        if current_user.is_authenticated:
            # Get notifications for the current user only
            user_notifications = Notification.query.filter_by(
                recipient_user_id=current_user.id
            ).order_by(Notification.created_at.desc()).all()
        else:
            # For guest users, check session-based notifications
            session_id = session.get('session_id')
            if session_id:
                user_notifications = Notification.query.filter_by(
                    recipient_session_id=session_id
                ).order_by(Notification.created_at.desc()).all()
            else:
                user_notifications = []
        
        return render_template('notifications.html', notifications=user_notifications)
    except Exception as e:
        logging.error(f"Error loading notifications: {e}")
        return render_template('notifications.html', notifications=[])

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Notification not found'}), 404
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notifications/mark-all-read', methods=['POST'])
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        if current_user.is_authenticated:
            Notification.query.filter_by(
                recipient_user_id=current_user.id,
                is_read=False
            ).update({Notification.is_read: True})
        else:
            session_id = session.get('session_id')
            if session_id:
                Notification.query.filter_by(
                    recipient_session_id=session_id,
                    is_read=False
                ).update({Notification.is_read: True})
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error marking all notifications as read: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/count')
def get_unread_notifications_count():
    """Get count of unread notifications"""
    try:
        if current_user.is_authenticated:
            count = Notification.query.filter_by(
                recipient_user_id=current_user.id,
                is_read=False
            ).count()
        else:
            session_id = session.get('session_id')
            if session_id:
                count = Notification.query.filter_by(
                    recipient_session_id=session_id,
                    is_read=False
                ).count()
            else:
                count = 0
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logging.error(f"Error getting notification count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/borrow-request/<int:book_id>/approve', methods=['POST'])
@login_required
def approve_borrow_request(book_id):
    """Approve a borrow request with agreed due date"""
    try:
        data = request.get_json()
        borrower_id = data.get('borrower_id')
        agreed_due_date = data.get('agreed_due_date')
        
        # Find the borrow request
        borrow_record = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=borrower_id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_record:
            return jsonify({'success': False, 'message': 'Borrow request not found'}), 404
        
        # Verify current user owns the book
        book = Book.query.get(book_id)
        if not book or book.posted_by != current_user.id:
            return jsonify({'success': False, 'message': 'You are not authorized to approve this request'}), 403
        
        # Update the borrow record
        if agreed_due_date:
            borrow_record.agreed_due_date = datetime.fromisoformat(agreed_due_date.replace('Z', '+00:00'))
            borrow_record.due_date = borrow_record.agreed_due_date
        
        borrow_record.is_agreed = True
        
        # Create approval notification for borrower
        borrower = User.query.get(borrower_id)
        if borrower:
            notification = Notification()
            notification.book_id = book_id
            notification.recipient_user_id = borrower_id
            notification.borrower_name = current_user.get_full_name() or current_user.username
            notification.message = f'Your request to borrow "{book.title}" has been approved!'
            notification.notification_type = 'borrow_approved'
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Borrow request approved successfully'})
        
    except Exception as e:
        logging.error(f"Error approving borrow request: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/borrow-request/<int:book_id>/reject', methods=['POST'])
@login_required
def reject_borrow_request(book_id):
    """Reject a borrow request"""
    try:
        data = request.get_json()
        borrower_id = data.get('borrower_id')
        reason = data.get('reason', 'No reason provided')
        
        # Find the borrow request
        borrow_record = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=borrower_id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_record:
            return jsonify({'success': False, 'message': 'Borrow request not found'}), 404
        
        # Verify current user owns the book
        book = Book.query.get(book_id)
        if not book or book.posted_by != current_user.id:
            return jsonify({'success': False, 'message': 'You are not authorized to reject this request'}), 403
        
        # Remove the borrow record
        db.session.delete(borrow_record)
        
        # Create rejection notification for borrower
        borrower = User.query.get(borrower_id)
        if borrower:
            notification = Notification()
            notification.book_id = book_id
            notification.recipient_user_id = borrower_id
            notification.borrower_name = current_user.get_full_name() or current_user.username
            notification.message = f'Your request to borrow "{book.title}" was declined. Reason: {reason}'
            notification.notification_type = 'borrow_rejected'
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Borrow request rejected'})
        
    except Exception as e:
        logging.error(f"Error rejecting borrow request: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/cancel_borrow_request/<int:book_id>', methods=['POST'])
@login_required
def cancel_borrow_request(book_id):
    """Cancel user's own borrow request"""
    try:
        # Find the user's pending borrow request
        borrow_record = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_record:
            return jsonify({'success': False, 'message': 'Borrow request not found'}), 404
        
        # Delete the borrow request
        db.session.delete(borrow_record)
        db.session.commit()
        
        # Get book details for the response
        book = Book.query.get(book_id)
        book_title = book.title if book else "Unknown Book"
        
        logging.info(f"Cancelled borrow request for book {book_id} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': f'Cancelled borrow request for "{book_title}"'
        })
        
    except Exception as e:
        logging.error(f"Error cancelling borrow request: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to cancel request'}), 500


@app.route('/book/<int:book_id>/discussion', methods=['GET', 'POST'])
def book_discussion(book_id):
    """Book-specific discussion page"""
    # Get the book first
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        try:
            message = request.form.get('message', '').strip()
            if not message:
                flash('Please enter a message.', 'warning')
                return redirect(url_for('book_discussion', book_id=book_id))
            
            # Get username
            if current_user.is_authenticated:
                username = current_user.get_full_name() or current_user.username
                user_id = current_user.id
                session_id = None
            else:
                username = request.form.get('username', '').strip()
                if not username:
                    flash('Please enter your name.', 'warning')
                    return redirect(url_for('book_discussion', book_id=book_id))
                user_id = None
                session_id = get_user_identifier()
            
            # Create discussion entry for this book
            discussion_entry = Discussion()
            discussion_entry.message = message
            discussion_entry.username = username
            discussion_entry.user_id = user_id
            discussion_entry.session_id = session_id
            discussion_entry.book_id = book_id
            
            db.session.add(discussion_entry)
            db.session.commit()
            
            return redirect(url_for('book_discussion', book_id=book_id))
        except Exception as e:
            logging.error(f"Error posting book discussion message: {e}")
            db.session.rollback()
            flash('Error posting message. Please try again.', 'error')
            return redirect(url_for('book_discussion', book_id=book_id))
    
    # GET request - display book discussion
    try:
        messages = Discussion.query.filter_by(book_id=book_id).order_by(Discussion.created_at.asc()).all()
        return render_template('book_discussion.html', messages=messages, book=book)
    except Exception as e:
        logging.error(f"Error loading book discussion: {e}")
        return render_template('book_discussion.html', messages=[], book=book)

@app.route('/poster/<int:user_id>')
def view_poster(user_id):
    """View poster profile page"""
    try:
        logging.info(f"View poster called with user_id: {user_id}")
        poster = User.query.get(user_id)
        if not poster:
            logging.error(f"User with ID {user_id} not found")
            return render_template('404.html'), 404
            
        logging.info(f"Found poster: {poster.username} (ID: {poster.id})")
        
        # Get books posted by this user
        posted_books = Book.query.filter_by(posted_by=user_id).order_by(Book.created_at.desc()).all()
        logging.info(f"Found {len(posted_books)} books posted by this user")
        
        return render_template('poster_profile.html', poster=poster, posted_books=posted_books)
    except Exception as e:
        logging.error(f"Error loading poster profile: {e}")
        return render_template('404.html'), 404

@app.route('/chat/<int:recipient_id>')
@app.route('/chat/<int:recipient_id>/<int:book_id>')
@login_required
def private_chat(recipient_id, book_id=None):
    """Private chat page with another user, optionally about a specific book"""
    try:
        recipient = User.query.get(recipient_id)
        if not recipient:
            return render_template('404.html'), 404
        
        # Get book context if book_id is provided
        book = None
        if book_id:
            book = Book.query.get(book_id)
            
        # Get chat history between current user and recipient
        messages = PrivateMessage.query.filter(
            ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == recipient_id)) |
            ((PrivateMessage.sender_id == recipient_id) & (PrivateMessage.recipient_id == current_user.id))
        ).order_by(PrivateMessage.created_at.asc()).all()
        
        # Mark messages as read
        PrivateMessage.query.filter_by(
            sender_id=recipient_id,
            recipient_id=current_user.id,
            is_read=False
        ).update({PrivateMessage.is_read: True})
        db.session.commit()
        
        return render_template('private_chat.html', recipient=recipient, messages=messages, book=book)
    except Exception as e:
        logging.error(f"Error loading private chat: {e}")
        return render_template('404.html'), 404

@app.route('/chat/<int:recipient_id>/send', methods=['POST'])
@login_required
def send_private_message(recipient_id):
    """Send a private message"""
    try:
        data = request.get_json()
        message_text = data.get('message', '').strip()
        book_id = data.get('book_id')
        
        if not message_text:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
            
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404
            
        # Create new message
        message = PrivateMessage()
        message.sender_id = current_user.id
        message.recipient_id = recipient_id
        message.message = message_text
        if book_id:
            message.book_id = book_id
            
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
    except Exception as e:
        logging.error(f"Error sending private message: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/<int:recipient_id>/messages')
@login_required
def get_chat_messages(recipient_id):
    """Get chat messages for real-time updates"""
    try:
        messages = PrivateMessage.query.filter(
            ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == recipient_id)) |
            ((PrivateMessage.sender_id == recipient_id) & (PrivateMessage.recipient_id == current_user.id))
        ).order_by(PrivateMessage.created_at.asc()).all()
        
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        logging.error(f"Error fetching chat messages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    """Add or update a review for a book"""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            rating = data.get('rating')
            review_text = data.get('review_text', '').strip()
            
            # Validate rating
            if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({'success': False, 'message': 'Rating must be between 1 and 5 stars'}), 400
            
            # Check if user already reviewed this book
            existing_review = BookReview.query.filter_by(
                book_id=book_id, 
                user_id=current_user.id
            ).first()
            
            if existing_review:
                # Update existing review
                existing_review.rating = rating
                existing_review.review_text = review_text
                existing_review.updated_at = datetime.utcnow()
            else:
                # Create new review
                review = BookReview(
                    book_id=book_id,
                    user_id=current_user.id,
                    rating=rating,
                    review_text=review_text
                )
                db.session.add(review)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Review submitted successfully!'
            })
            
        except Exception as e:
            logging.error(f"Error adding review: {e}")
            return jsonify({'success': False, 'message': 'Failed to submit review'}), 500
    
    # GET request - show review form
    user_review = BookReview.query.filter_by(
        book_id=book_id, 
        user_id=current_user.id
    ).first()
    
    return render_template('book_detail.html', 
                         book=book, 
                         user_review=user_review,
                         datetime=datetime,
                         timedelta=timedelta)

@app.route('/book/<int:book_id>/reviews')
def get_reviews(book_id):
    """Get all reviews for a book"""
    try:
        reviews = BookReview.query.filter_by(book_id=book_id).order_by(BookReview.created_at.desc()).all()
        return jsonify({
            'success': True,
            'reviews': [review.to_dict() for review in reviews]
        })
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/review/<int:review_id>/delete', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """Delete a review (only by the author)"""
    try:
        review = BookReview.query.get_or_404(review_id)
        
        # Check if current user owns this review
        if review.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'You can only delete your own reviews'}), 403
        
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Review deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting review: {e}")
        return jsonify({'success': False, 'message': 'Failed to delete review'}), 500


# Achievement System Functions
def check_and_award_achievements(user_id):
    """Check if user has earned any new achievements and award them"""
    try:
        from models import Achievement, UserAchievement
        
        # Get all achievements that this user hasn't earned yet
        unlocked_achievement_ids = db.session.query(UserAchievement.achievement_id).filter_by(user_id=user_id).all()
        unlocked_ids = [ua.achievement_id for ua in unlocked_achievement_ids]
        
        available_achievements = Achievement.query.filter(
            Achievement.is_active == True,
            ~Achievement.id.in_(unlocked_ids)
        ).all()
        
        newly_unlocked = []
        
        for achievement in available_achievements:
            if check_achievement_requirement(user_id, achievement):
                # Award the achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    is_seen=False
                )
                db.session.add(user_achievement)
                newly_unlocked.append(achievement)
        
        if newly_unlocked:
            db.session.commit()
            logging.info(f"Awarded {len(newly_unlocked)} new achievements to user {user_id}")
        
        return newly_unlocked
        
    except Exception as e:
        logging.error(f"Error checking achievements for user {user_id}: {e}")
        return []


def check_achievement_requirement(user_id, achievement):
    """Check if user meets the requirement for a specific achievement"""
    try:
        from models import BorrowedBook, BookReview, Discussion, PrivateMessage
        
        if achievement.requirement_type == 'count':
            if achievement.category == 'books':
                # Count books borrowed and returned
                count = BorrowedBook.query.filter_by(
                    user_id=user_id,
                    is_returned=True
                ).count()
                return count >= achievement.requirement_value
                
            elif achievement.category == 'reviews':
                # Count reviews written
                count = BookReview.query.filter_by(user_id=user_id).count()
                return count >= achievement.requirement_value
                
            elif achievement.category == 'social':
                # Count discussion messages
                count = Discussion.query.filter_by(user_id=user_id).count()
                return count >= achievement.requirement_value
                
        elif achievement.requirement_type == 'streak':
            # For streak achievements, we'd need to implement streak tracking
            # This is a placeholder for now
            return False
            
        elif achievement.requirement_type == 'special':
            # Special achievements with custom logic
            if achievement.name == 'First Steps':
                # User has logged in (they exist in the system)
                return True
            elif achievement.name == 'Bookworm':
                # User has borrowed at least 10 books
                count = BorrowedBook.query.filter_by(user_id=user_id).count()
                return count >= 10
            elif achievement.name == 'Critic':
                # User has written at least 5 reviews
                count = BookReview.query.filter_by(user_id=user_id).count()
                return count >= 5
            elif achievement.name == 'Social Butterfly':
                # User has sent at least 20 messages
                count = PrivateMessage.query.filter_by(sender_id=user_id).count()
                return count >= 20
        
        return False
        
    except Exception as e:
        logging.error(f"Error checking achievement requirement: {e}")
        return False


def get_user_achievements(user_id):
    """Get all achievements for a user"""
    try:
        from models import UserAchievement, Achievement
        
        user_achievements = db.session.query(UserAchievement, Achievement).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).filter(UserAchievement.user_id == user_id).order_by(
            UserAchievement.unlocked_at.desc()
        ).all()
        
        achievements = []
        for user_ach, achievement in user_achievements:
            ach_dict = achievement.to_dict()
            ach_dict['unlocked_at'] = user_ach.unlocked_at.isoformat() if user_ach.unlocked_at else None
            ach_dict['is_seen'] = user_ach.is_seen
            ach_dict['time_ago'] = user_ach.get_time_ago()
            achievements.append(ach_dict)
        
        return achievements
        
    except Exception as e:
        logging.error(f"Error getting user achievements: {e}")
        return []


def get_achievement_progress(user_id):
    """Get progress towards all achievements for a user"""
    try:
        from models import Achievement, UserAchievement, BorrowedBook, BookReview, Discussion, PrivateMessage
        
        # Get unlocked achievements
        unlocked_achievement_ids = db.session.query(UserAchievement.achievement_id).filter_by(user_id=user_id).all()
        unlocked_ids = [ua.achievement_id for ua in unlocked_achievement_ids]
        
        # Get all achievements
        all_achievements = Achievement.query.filter(Achievement.is_active == True).all()
        
        progress = []
        
        for achievement in all_achievements:
            is_unlocked = achievement.id in unlocked_ids
            current_progress = 0
            
            if not is_unlocked:
                # Calculate current progress
                if achievement.requirement_type == 'count':
                    if achievement.category == 'books':
                        current_progress = BorrowedBook.query.filter_by(
                            user_id=user_id,
                            is_returned=True
                        ).count()
                    elif achievement.category == 'reviews':
                        current_progress = BookReview.query.filter_by(user_id=user_id).count()
                    elif achievement.category == 'social':
                        current_progress = Discussion.query.filter_by(user_id=user_id).count()
                elif achievement.requirement_type == 'special':
                    current_progress = 1 if check_achievement_requirement(user_id, achievement) else 0
            else:
                current_progress = achievement.requirement_value
            
            progress.append({
                'achievement': achievement.to_dict(),
                'current_progress': current_progress,
                'max_progress': achievement.requirement_value,
                'is_unlocked': is_unlocked,
                'progress_percentage': min(100, (current_progress / achievement.requirement_value) * 100)
            })
        
        return progress
        
    except Exception as e:
        logging.error(f"Error getting achievement progress: {e}")
        return []


@app.route('/achievements')
@login_required
def achievements():
    """Display user's achievements page"""
    # Check for new achievements when user visits the page
    check_and_award_achievements(current_user.id)
    
    user_achievements = get_user_achievements(current_user.id)
    achievement_progress = get_achievement_progress(current_user.id)
    
    # Mark all achievements as seen
    from models import UserAchievement
    UserAchievement.query.filter_by(user_id=current_user.id, is_seen=False).update({'is_seen': True})
    db.session.commit()
    
    return render_template('achievements.html', 
                         user_achievements=user_achievements,
                         achievement_progress=achievement_progress)


@app.route('/ranks')
@login_required
def ranks():
    """Display user ranks and leaderboard"""
    # Get current user's rank info
    user_rank_info = current_user.get_rank_info()
    
    # Get all ranks for display
    ranks = [
        {'name': 'Newbie', 'min_points': 0, 'max_points': 49, 'color': '#6c757d', 'icon': 'fa-seedling'},
        {'name': 'Reader', 'min_points': 50, 'max_points': 149, 'color': '#17a2b8', 'icon': 'fa-book'},
        {'name': 'Bookworm', 'min_points': 150, 'max_points': 299, 'color': '#28a745', 'icon': 'fa-book-open'},
        {'name': 'Scholar', 'min_points': 300, 'max_points': 499, 'color': '#ffc107', 'icon': 'fa-graduation-cap'},
        {'name': 'Expert', 'min_points': 500, 'max_points': 799, 'color': '#fd7e14', 'icon': 'fa-award'},
        {'name': 'Master', 'min_points': 800, 'max_points': 1199, 'color': '#e83e8c', 'icon': 'fa-crown'},
        {'name': 'Grandmaster', 'min_points': 1200, 'max_points': 1999, 'color': '#6f42c1', 'icon': 'fa-gem'},
        {'name': 'Legend', 'min_points': 2000, 'max_points': 99999, 'color': '#dc3545', 'icon': 'fa-trophy'}
    ]
    
    # Get leaderboard - top 10 users by points
    from models import User, UserAchievement, Achievement
    leaderboard = db.session.query(
        User.id, 
        User.username,
        User.first_name,
        User.last_name,
        db.func.sum(Achievement.points).label('total_points')
    ).join(
        UserAchievement, User.id == UserAchievement.user_id
    ).join(
        Achievement, UserAchievement.achievement_id == Achievement.id
    ).group_by(User.id).order_by(db.desc('total_points')).limit(10).all()
    
    # Add rank info for each user in leaderboard
    leaderboard_with_ranks = []
    for user_data in leaderboard:
        user_obj = User.query.get(user_data.id)
        user_rank = user_obj.get_rank_info()
        leaderboard_with_ranks.append({
            'user': user_obj,
            'rank_info': user_rank
        })
    
    return render_template('ranks.html', 
                         user_rank_info=user_rank_info,
                         ranks=ranks,
                         leaderboard=leaderboard_with_ranks)


@app.route('/api/achievements/check', methods=['POST'])
@login_required
def check_achievements_api():
    """API endpoint to check for new achievements"""
    new_achievements = check_and_award_achievements(current_user.id)
    return jsonify({
        'success': True,
        'new_achievements': [ach.to_dict() for ach in new_achievements]
    })


@app.route('/profile')
@login_required
def profile():
    """User profile customization page"""
    # Get or create user profile
    user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not user_profile:
        user_profile = UserProfile()
        user_profile.user_id = current_user.id
        db.session.add(user_profile)
        db.session.commit()
    
    return render_template('profile.html', profile=user_profile)


@app.route('/save_profile', methods=['POST'])
@login_required
def save_profile():
    """Save profile customization changes"""
    try:
        data = request.get_json()
        
        # Get costs
        cost = data.get('cost', 0)
        
        # Check if user has enough points
        user_points = current_user.get_total_points()
        if cost > user_points:
            return jsonify({
                'success': False,
                'message': f'Not enough points! You need {cost} points but only have {user_points}.'
            }), 400
        
        # Get or create user profile
        user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not user_profile:
            user_profile = UserProfile()
            user_profile.user_id = current_user.id
            db.session.add(user_profile)
        
        # Update profile
        user_profile.banner_style = data.get('banner_style')
        user_profile.custom_title = data.get('custom_title')
        user_profile.title_color = data.get('title_color', '#ffffff')
        user_profile.updated_at = datetime.utcnow()
        
        # For point spending, we'll use a simple approach - just track in logs
        # In a real app, you'd want a proper points/currency system
        
        db.session.commit()
        
        logging.info(f"Profile updated for user {current_user.id}, cost: {cost} points")
        
        return jsonify({
            'success': True,
            'message': f'Profile updated successfully! Spent {cost} points.',
            'remaining_points': user_points - cost
        })
        
    except Exception as e:
        logging.error(f"Error saving profile: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to save profile changes'
        }), 500


@app.route('/seed_achievements')
def seed_achievements():
    """Seed the database with sample achievements"""
    try:
        from models import Achievement
        
        # Clear existing achievements
        Achievement.query.delete()
        db.session.commit()
        
        # Define sample achievements
        sample_achievements = [
            {
                'name': 'First Steps',
                'description': 'Welcome to L.E.A.F! You\'ve joined our reading community.',
                'icon': 'fa-star',
                'category': 'special',
                'requirement_type': 'special',
                'requirement_value': 1,
                'points': 10
            },
            {
                'name': 'Bookworm',
                'description': 'Borrow your first book from the library.',
                'icon': 'fa-book',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 1,
                'points': 15
            },
            {
                'name': 'Avid Reader',
                'description': 'Complete reading 5 books.',
                'icon': 'fa-book-open',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 5,
                'points': 25
            },
            {
                'name': 'Library Master',
                'description': 'Complete reading 25 books.',
                'icon': 'fa-crown',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 25,
                'points': 50
            },
            {
                'name': 'Critic',
                'description': 'Write your first book review.',
                'icon': 'fa-pen',
                'category': 'reviews',
                'requirement_type': 'count',
                'requirement_value': 1,
                'points': 15
            },
            {
                'name': 'Review Expert',
                'description': 'Write 10 insightful book reviews.',
                'icon': 'fa-star-half-alt',
                'category': 'reviews',
                'requirement_type': 'count',
                'requirement_value': 10,
                'points': 30
            },
            {
                'name': 'Social Butterfly',
                'description': 'Participate in 10 book discussions.',
                'icon': 'fa-comments',
                'category': 'social',
                'requirement_type': 'count',
                'requirement_value': 10,
                'points': 20
            },
            {
                'name': 'Conversation Starter',
                'description': 'Send your first private message to another reader.',
                'icon': 'fa-comment-dots',
                'category': 'social',
                'requirement_type': 'special',
                'requirement_value': 1,
                'points': 15
            },
            {
                'name': 'Speed Reader',
                'description': 'Return 3 books in the same week.',
                'icon': 'fa-tachometer-alt',
                'category': 'time',
                'requirement_type': 'streak',
                'requirement_value': 3,
                'points': 35
            },
            {
                'name': 'Book Collector',
                'description': 'Borrow books from 5 different categories.',
                'icon': 'fa-layer-group',
                'category': 'books',
                'requirement_type': 'special',
                'requirement_value': 5,
                'points': 25
            }
        ]
        
        # Add achievements to database
        for ach_data in sample_achievements:
            achievement = Achievement(**ach_data)
            db.session.add(achievement)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully seeded {len(sample_achievements)} achievements'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding achievements: {e}")
        return jsonify({'success': False, 'message': f'Error seeding achievements: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
