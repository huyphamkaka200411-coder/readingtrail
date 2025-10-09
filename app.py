"""
L.E.A.F - Digital Book Borrowing System
Main application file following MVC pattern
"""
import os
import logging
from datetime import datetime
from flask import session, render_template
from flask_login import UserMixin, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config import create_app, db, login_manager

# Import models after db is initialized
from models import (
    User, Book, BorrowedBook, Discussion, Notification, 
    PrivateMessage, BookReview, Achievement, UserAchievement, UserProfile,
    PowerUp, UserPowerUp
)

# Import controllers
from controllers import (
    auth_controller, book_controller, social_controller, 
    review_controller, achievement_controller, translation_controller
)
from controllers.api_controller import api_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create app
app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Register API blueprint
app.register_blueprint(api_bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor for global template variables
@app.context_processor
def inject_borrowed_count():
    """Inject borrowed count and notification count into all templates"""
    from datetime import datetime, timedelta
    
    borrowed_count = 0
    notification_count = 0
    
    if current_user.is_authenticated:
        # Update user activity on each request
        current_user.update_activity()
        db.session.commit()
        
        borrowed_count = len(book_controller.get_borrowed_books())
        try:
            notification_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
        except Exception as e:
            logging.error(f"Error getting notification count: {e}")
            notification_count = 0
    
    return dict(
        borrowed_count=borrowed_count,
        notification_count=notification_count,
        datetime=datetime,
        timedelta=timedelta
    )

# Translation template filter
@app.template_filter('translate')
def translate_filter(key):
    """Template filter for translations"""
    return translation_controller.get_translation(key)

# Context processor for current language
@app.context_processor
def inject_language():
    """Inject current language into all templates"""
    if 'language' not in session:
        session['language'] = 'vi'
    
    return dict(
        current_language=session.get('language', 'vi')
    )

# Helper function for session management
def get_user_identifier():
    """Get user ID if logged in, otherwise session ID"""
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    else:
        if 'session_id' not in session:
            import uuid
            session['session_id'] = str(uuid.uuid4())
        return f"session_{session['session_id']}"

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_controller.login()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return auth_controller.signup()

@app.route('/logout')
def logout():
    return auth_controller.logout()

# Book routes
@app.route('/')
def index():
    return book_controller.index()

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    return book_controller.book_detail(book_id)

@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow_book(book_id):
    return book_controller.borrow_book(book_id)

@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    return book_controller.return_book(book_id)

@app.route('/dashboard')
def dashboard():
    return book_controller.dashboard()

@app.route('/post_book', methods=['GET', 'POST'])
def post_book():
    return book_controller.post_book()

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    return book_controller.post_book()

@app.route('/seed_books')
def seed_books():
    return book_controller.seed_books()

# Social routes
@app.route('/discussion', methods=['GET', 'POST'])
def discussion():
    return social_controller.discussion()

@app.route('/api/discussion/messages')
def get_discussion_messages():
    return social_controller.get_discussion_messages()

@app.route('/book/<int:book_id>/discussion', methods=['GET', 'POST'])
def book_discussion(book_id):
    return social_controller.book_discussion(book_id)

@app.route('/poster/<int:user_id>')
def view_poster(user_id):
    return social_controller.view_poster(user_id)

@app.route('/chat/<int:recipient_id>')
@app.route('/chat/<int:recipient_id>/<int:book_id>')
def private_chat(recipient_id, book_id=None):
    return social_controller.private_chat(recipient_id, book_id)

@app.route('/api/chat/<int:recipient_id>/send', methods=['POST'])
def send_private_message(recipient_id):
    return social_controller.send_private_message(recipient_id)

@app.route('/api/chat/<int:recipient_id>/messages')
def get_chat_messages(recipient_id):
    return social_controller.get_chat_messages(recipient_id)

@app.route('/notifications')
def notifications():
    return social_controller.notifications()

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    return social_controller.mark_notification_read(notification_id)

@app.route('/api/notifications/read_all', methods=['POST'])
def mark_all_notifications_read():
    return social_controller.mark_all_notifications_read()

@app.route('/api/notifications/count')
def get_unread_notifications_count():
    return social_controller.get_unread_notifications_count()

@app.route('/notifications/book-request/<int:notification_id>/<action>', methods=['POST'])
def handle_book_request_notification(notification_id, action):
    return social_controller.handle_book_request_notification(notification_id, action)

@app.route('/api/books/<int:book_id>/approve_borrow', methods=['POST'])
def approve_borrow_request(book_id):
    return social_controller.approve_borrow_request(book_id)

@app.route('/api/books/<int:book_id>/reject_borrow', methods=['POST'])
def reject_borrow_request(book_id):
    return social_controller.reject_borrow_request(book_id)

@app.route('/api/books/<int:book_id>/cancel_borrow', methods=['POST'])
def cancel_borrow_request(book_id):
    return social_controller.cancel_borrow_request(book_id)

# Review routes
@app.route('/api/books/<int:book_id>/reviews', methods=['POST'])
def add_review(book_id):
    return review_controller.add_review(book_id)

@app.route('/api/books/<int:book_id>/reviews')
def get_reviews(book_id):
    return review_controller.get_reviews(book_id)

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    return review_controller.delete_review(review_id)

# Achievement routes
@app.route('/achievements')
def achievements():
    return achievement_controller.achievements()

@app.route('/ranks')
def ranks():
    return achievement_controller.ranks()

@app.route('/api/achievements/check', methods=['POST'])
def check_achievements_api():
    return achievement_controller.check_achievements_api()

@app.route('/profile')
def profile():
    
    return achievement_controller.profile()

@app.route('/save_profile', methods=['POST'])
def save_profile():
    return achievement_controller.save_profile()

@app.route('/seed_achievements')
def seed_achievements():
    return achievement_controller.seed_achievements()

# Store routes
@app.route('/store')
def store():
    from controllers import store_controller
    return store_controller.store()

@app.route('/purchase_powerup', methods=['POST'])
def purchase_powerup():
    from controllers import store_controller
    return store_controller.purchase_powerup()

@app.route('/activate_powerup', methods=['POST'])
def activate_powerup():
    from controllers import store_controller
    return store_controller.activate_powerup()

@app.route('/seed_powerups')
def seed_powerups():
    from controllers import store_controller
    return store_controller.seed_powerups()

@app.route('/info')
def info():
    """Display information about L.E.A.F platform"""
    return render_template('info.html')

@app.route('/achievements-guide')
def achievements_guide():
    """Display guide on how to earn achievements and points"""
    return render_template('achievements_guide.html')

# Translation routes
@app.route('/translate', methods=['GET', 'POST'])
def translate_admin():
    """Translation management admin page"""
    return translation_controller.translate_admin()

@app.route('/delete_translation', methods=['POST'])
def delete_translation():
    """Delete a translation"""
    return translation_controller.delete_translation()

@app.route('/toggle_language')
def toggle_language():
    """Toggle between languages"""
    return translation_controller.toggle_language()

@app.route('/set_language/<lang>')
def set_language(lang):
    """Set language"""
    return translation_controller.set_language(lang)

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)