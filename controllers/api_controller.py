"""
REST API Controller
Provides RESTful web services for all models following standard REST conventions.
"""
from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from config import db
from models import (
    User, Book, BorrowedBook, BookReview, 
    Achievement, UserAchievement, Discussion, 
    PrivateMessage, Notification
)
import logging

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Helper function for error responses
def error_response(message, status_code=400):
    return jsonify({'error': message}), status_code

def success_response(data=None, message='Success', status_code=200):
    response = {'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

# Helper function to serialize datetime objects
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# ============================================================================
# USER API ENDPOINTS
# ============================================================================

@api_bp.route('/users', methods=['GET'])
def get_users():
    """GET /api/v1/users - List all users with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                User.username.ilike(f'%{search}%') |
                User.email.ilike(f'%{search}%') |
                User.first_name.ilike(f'%{search}%') |
                User.last_name.ilike(f'%{search}%')
            )
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'users': [{
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
                'active': user.active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'total_points': user.get_total_points(),
                'rank_info': user.get_rank_info()
            } for user in users.items],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return error_response('Failed to fetch users', 500)

@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """GET /api/v1/users/{id} - Get specific user by ID"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'active': user.active,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'total_points': user.get_total_points(),
            'rank_info': user.get_rank_info(),
            'borrowed_books_count': len(user.borrowed_books),
            'posted_books_count': len(user.posted_books)
        }
        
        return success_response(user_data)
        
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {e}")
        return error_response('Failed to fetch user', 500)

@api_bp.route('/users', methods=['POST'])
def create_user():
    """POST /api/v1/users - Create a new user"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing required field: {field}')
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return error_response('Username already exists')
        
        if User.query.filter_by(email=data['email']).first():
            return error_response('Email already exists')
        
        # Create new user
        user = User()
        user.username = data['username']
        user.email = data['email']
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': user.created_at.isoformat()
        }
        
        return success_response(user_data, 'User created successfully', 201)
        
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        db.session.rollback()
        return error_response('Failed to create user', 500)

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """PUT /api/v1/users/{id} - Update a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        # Users can only update their own profile (unless admin)
        if current_user.id != user_id:
            return error_response('Access denied', 403)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email already exists for another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return error_response('Email already exists')
            user.email = data['email']
        
        db.session.commit()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name()
        }
        
        return success_response(user_data, 'User updated successfully')
        
    except Exception as e:
        logging.error(f"Error updating user {user_id}: {e}")
        db.session.rollback()
        return error_response('Failed to update user', 500)

# ============================================================================
# BOOK API ENDPOINTS
# ============================================================================

@api_bp.route('/books', methods=['GET'])
def get_books():
    """GET /api/v1/books - List all books with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        query = Book.query
        
        if search:
            query = query.filter(
                Book.title.ilike(f'%{search}%') |
                Book.author.ilike(f'%{search}%') |
                Book.description.ilike(f'%{search}%')
            )
        
        if category:
            query = query.filter(Book.category == category)
        
        if available_only:
            query = query.filter(Book.available == True)
        
        books = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'books': [book.to_dict() for book in books.items],
            'pagination': {
                'page': books.page,
                'pages': books.pages,
                'per_page': books.per_page,
                'total': books.total,
                'has_next': books.has_next,
                'has_prev': books.has_prev
            }
        }
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching books: {e}")
        return error_response('Failed to fetch books', 500)

@api_bp.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """GET /api/v1/books/{id} - Get specific book by ID"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        book_data = book.to_dict()
        book_data['average_rating'] = book.get_average_rating()
        book_data['review_count'] = book.get_review_count()
        
        # Add poster information
        if book.poster:
            book_data['poster_info'] = {
                'id': book.poster.id,
                'username': book.poster.username,
                'full_name': book.poster.get_full_name()
            }
        
        return success_response(book_data)
        
    except Exception as e:
        logging.error(f"Error fetching book {book_id}: {e}")
        return error_response('Failed to fetch book', 500)

@api_bp.route('/books', methods=['POST'])
@login_required
def create_book():
    """POST /api/v1/books - Create a new book"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'author', 'category', 'isbn']
        for field in required_fields:
            if field not in data:
                return error_response(f'Missing required field: {field}')
        
        # Check if ISBN already exists
        if Book.query.filter_by(isbn=data['isbn']).first():
            return error_response('Book with this ISBN already exists')
        
        # Create new book
        book = Book()
        book.title = data['title']
        book.author = data['author']
        book.category = data['category']
        book.isbn = data['isbn']
        book.description = data.get('description')
        book.cover_url = data.get('cover_url')
        book.publication_year = data.get('publication_year')
        book.pages = data.get('pages')
        book.posted_by = current_user.id
        
        db.session.add(book)
        db.session.commit()
        
        return success_response(book.to_dict(), 'Book created successfully', 201)
        
    except Exception as e:
        logging.error(f"Error creating book: {e}")
        db.session.rollback()
        return error_response('Failed to create book', 500)

@api_bp.route('/books/<int:book_id>', methods=['PUT'])
@login_required
def update_book(book_id):
    """PUT /api/v1/books/{id} - Update a book"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        # Only the poster can update the book
        if current_user.id != book.posted_by:
            return error_response('Access denied', 403)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            book.title = data['title']
        if 'author' in data:
            book.author = data['author']
        if 'category' in data:
            book.category = data['category']
        if 'description' in data:
            book.description = data['description']
        if 'cover_url' in data:
            book.cover_url = data['cover_url']
        if 'publication_year' in data:
            book.publication_year = data['publication_year']
        if 'pages' in data:
            book.pages = data['pages']
        if 'available' in data:
            book.available = data['available']
        
        db.session.commit()
        
        return success_response(book.to_dict(), 'Book updated successfully')
        
    except Exception as e:
        logging.error(f"Error updating book {book_id}: {e}")
        db.session.rollback()
        return error_response('Failed to update book', 500)

@api_bp.route('/books/<int:book_id>', methods=['DELETE'])
@login_required
def delete_book(book_id):
    """DELETE /api/v1/books/{id} - Delete a book"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        # Only the poster can delete the book
        if current_user.id != book.posted_by:
            return error_response('Access denied', 403)
        
        db.session.delete(book)
        db.session.commit()
        
        return success_response(message='Book deleted successfully')
        
    except Exception as e:
        logging.error(f"Error deleting book {book_id}: {e}")
        db.session.rollback()
        return error_response('Failed to delete book', 500)

# ============================================================================
# BORROWED BOOKS API ENDPOINTS
# ============================================================================

@api_bp.route('/borrowed-books', methods=['GET'])
@login_required
def get_borrowed_books():
    """GET /api/v1/borrowed-books - Get current user's borrowed books"""
    try:
        borrowed_books = BorrowedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False
        ).all()
        
        result = [{
            'id': bb.id,
            'book': bb.book.to_dict() if bb.book else None,
            'borrowed_date': bb.borrowed_date.isoformat() if bb.borrowed_date else None,
            'due_date': bb.due_date.isoformat() if bb.due_date else None,
            'is_agreed': bb.is_agreed,
            'is_overdue': bb.is_overdue() if hasattr(bb, 'is_overdue') else False
        } for bb in borrowed_books]
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching borrowed books: {e}")
        return error_response('Failed to fetch borrowed books', 500)

@api_bp.route('/books/<int:book_id>/borrow', methods=['POST'])
@login_required
def borrow_book(book_id):
    """POST /api/v1/books/{id}/borrow - Borrow a book"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        if not book.available:
            return error_response('Book is not available')
        
        # Check if user already borrowed this book
        existing_borrow = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False
        ).first()
        
        if existing_borrow:
            return error_response('You have already borrowed this book')
        
        # Create borrow record
        due_date = datetime.utcnow() + timedelta(days=14)  # 2 weeks loan
        borrowed_book = BorrowedBook()
        borrowed_book.book_id = book_id
        borrowed_book.user_id = current_user.id
        borrowed_book.due_date = due_date
        
        book.available = False
        db.session.add(borrowed_book)
        db.session.commit()
        
        return success_response({
            'id': borrowed_book.id,
            'book_id': book_id,
            'due_date': due_date.isoformat()
        }, 'Book borrowed successfully', 201)
        
    except Exception as e:
        logging.error(f"Error borrowing book {book_id}: {e}")
        db.session.rollback()
        return error_response('Failed to borrow book', 500)

@api_bp.route('/borrowed-books/<int:borrow_id>/return', methods=['POST'])
@login_required
def return_book(borrow_id):
    """POST /api/v1/borrowed-books/{id}/return - Return a borrowed book"""
    try:
        borrowed_book = BorrowedBook.query.get(borrow_id)
        if not borrowed_book:
            return error_response('Borrow record not found', 404)
        
        if borrowed_book.user_id != current_user.id:
            return error_response('Access denied', 403)
        
        if borrowed_book.is_returned:
            return error_response('Book is already returned')
        
        # Mark as returned
        borrowed_book.is_returned = True
        borrowed_book.returned_date = datetime.utcnow()
        borrowed_book.book.available = True
        
        db.session.commit()
        
        return success_response(message='Book returned successfully')
        
    except Exception as e:
        logging.error(f"Error returning book {borrow_id}: {e}")
        db.session.rollback()
        return error_response('Failed to return book', 500)

# ============================================================================
# BOOK REVIEWS API ENDPOINTS
# ============================================================================

@api_bp.route('/books/<int:book_id>/reviews', methods=['GET'])
def get_book_reviews(book_id):
    """GET /api/v1/books/{id}/reviews - Get reviews for a book"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        reviews = BookReview.query.filter_by(book_id=book_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'reviews': [review.to_dict() for review in reviews.items],
            'pagination': {
                'page': reviews.page,
                'pages': reviews.pages,
                'per_page': reviews.per_page,
                'total': reviews.total,
                'has_next': reviews.has_next,
                'has_prev': reviews.has_prev
            },
            'average_rating': book.get_average_rating()
        }
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching reviews for book {book_id}: {e}")
        return error_response('Failed to fetch reviews', 500)

@api_bp.route('/books/<int:book_id>/reviews', methods=['POST'])
@login_required
def create_book_review(book_id):
    """POST /api/v1/books/{id}/reviews - Create a review for a book"""
    try:
        book = Book.query.get(book_id)
        if not book:
            return error_response('Book not found', 404)
        
        data = request.get_json()
        
        if 'rating' not in data:
            return error_response('Rating is required')
        
        rating = data['rating']
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return error_response('Rating must be an integer between 1 and 5')
        
        # Check if user already reviewed this book
        existing_review = BookReview.query.filter_by(
            book_id=book_id,
            user_id=current_user.id
        ).first()
        
        if existing_review:
            return error_response('You have already reviewed this book')
        
        # Create review
        review = BookReview()
        review.book_id = book_id
        review.user_id = current_user.id
        review.rating = rating
        review.review_text = data.get('review_text')
        
        db.session.add(review)
        db.session.commit()
        
        return success_response(review.to_dict(), 'Review created successfully', 201)
        
    except Exception as e:
        logging.error(f"Error creating review for book {book_id}: {e}")
        db.session.rollback()
        return error_response('Failed to create review', 500)

@api_bp.route('/reviews/<int:review_id>', methods=['PUT'])
@login_required
def update_review(review_id):
    """PUT /api/v1/reviews/{id} - Update a review"""
    try:
        review = BookReview.query.get(review_id)
        if not review:
            return error_response('Review not found', 404)
        
        if review.user_id != current_user.id:
            return error_response('Access denied', 403)
        
        data = request.get_json()
        
        if 'rating' in data:
            rating = data['rating']
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return error_response('Rating must be an integer between 1 and 5')
            review.rating = rating
        
        if 'review_text' in data:
            review.review_text = data['review_text']
        
        review.updated_at = datetime.utcnow()
        db.session.commit()
        
        return success_response(review.to_dict(), 'Review updated successfully')
        
    except Exception as e:
        logging.error(f"Error updating review {review_id}: {e}")
        db.session.rollback()
        return error_response('Failed to update review', 500)

@api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    """DELETE /api/v1/reviews/{id} - Delete a review"""
    try:
        review = BookReview.query.get(review_id)
        if not review:
            return error_response('Review not found', 404)
        
        if review.user_id != current_user.id:
            return error_response('Access denied', 403)
        
        db.session.delete(review)
        db.session.commit()
        
        return success_response(message='Review deleted successfully')
        
    except Exception as e:
        logging.error(f"Error deleting review {review_id}: {e}")
        db.session.rollback()
        return error_response('Failed to delete review', 500)

# ============================================================================
# ACHIEVEMENTS API ENDPOINTS
# ============================================================================

@api_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """GET /api/v1/achievements - List all achievements"""
    try:
        achievements = Achievement.query.filter_by(is_active=True).all()
        
        result = [achievement.to_dict() for achievement in achievements]
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching achievements: {e}")
        return error_response('Failed to fetch achievements', 500)

@api_bp.route('/achievements/<int:achievement_id>', methods=['GET'])
def get_achievement(achievement_id):
    """GET /api/v1/achievements/{id} - Get specific achievement"""
    try:
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            return error_response('Achievement not found', 404)
        
        return success_response(achievement.to_dict())
        
    except Exception as e:
        logging.error(f"Error fetching achievement {achievement_id}: {e}")
        return error_response('Failed to fetch achievement', 500)

@api_bp.route('/users/<int:user_id>/achievements', methods=['GET'])
def get_user_achievements(user_id):
    """GET /api/v1/users/{id}/achievements - Get user's achievements"""
    try:
        user = User.query.get(user_id)
        if not user:
            return error_response('User not found', 404)
        
        user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
        
        result = [{
            'id': ua.id,
            'achievement': ua.achievement.to_dict() if ua.achievement else None,
            'unlocked_at': ua.unlocked_at.isoformat() if ua.unlocked_at else None,
            'is_seen': ua.is_seen
        } for ua in user_achievements]
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching achievements for user {user_id}: {e}")
        return error_response('Failed to fetch user achievements', 500)

# ============================================================================
# DISCUSSIONS API ENDPOINTS
# ============================================================================

@api_bp.route('/discussions', methods=['GET'])
def get_discussions():
    """GET /api/v1/discussions - List all discussions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        book_id = request.args.get('book_id', type=int)
        
        query = Discussion.query
        
        if book_id:
            query = query.filter_by(book_id=book_id)
        
        discussions = query.order_by(Discussion.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'discussions': [discussion.to_dict() for discussion in discussions.items],
            'pagination': {
                'page': discussions.page,
                'pages': discussions.pages,
                'per_page': discussions.per_page,
                'total': discussions.total,
                'has_next': discussions.has_next,
                'has_prev': discussions.has_prev
            }
        }
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching discussions: {e}")
        return error_response('Failed to fetch discussions', 500)

@api_bp.route('/discussions', methods=['POST'])
@login_required
def create_discussion():
    """POST /api/v1/discussions - Create a new discussion"""
    try:
        data = request.get_json()
        
        if 'message' not in data:
            return error_response('Message is required')
        
        discussion = Discussion()
        discussion.user_id = current_user.id
        discussion.username = current_user.username
        discussion.message = data['message']
        discussion.book_id = data.get('book_id')
        
        db.session.add(discussion)
        db.session.commit()
        
        return success_response(discussion.to_dict(), 'Discussion created successfully', 201)
        
    except Exception as e:
        logging.error(f"Error creating discussion: {e}")
        db.session.rollback()
        return error_response('Failed to create discussion', 500)

# ============================================================================
# NOTIFICATIONS API ENDPOINTS
# ============================================================================

@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """GET /api/v1/notifications - Get user's notifications"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        query = Notification.query.filter_by(user_id=current_user.id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'notifications': [notification.to_dict() for notification in notifications.items],
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
        }
        
        return success_response(result)
        
    except Exception as e:
        logging.error(f"Error fetching notifications: {e}")
        return error_response('Failed to fetch notifications', 500)

@api_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """PUT /api/v1/notifications/{id}/read - Mark notification as read"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return error_response('Notification not found', 404)
        
        if notification.user_id != current_user.id:
            return error_response('Access denied', 403)
        
        notification.is_read = True
        db.session.commit()
        
        return success_response(message='Notification marked as read')
        
    except Exception as e:
        logging.error(f"Error marking notification {notification_id} as read: {e}")
        db.session.rollback()
        return error_response('Failed to mark notification as read', 500)

# Register error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return error_response('Resource not found', 404)

@api_bp.errorhandler(400)
def bad_request(error):
    return error_response('Bad request', 400)

@api_bp.errorhandler(500)
def internal_error(error):
    return error_response('Internal server error', 500)