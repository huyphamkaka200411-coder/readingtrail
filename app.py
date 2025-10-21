import os
import logging
from datetime import datetime
from flask import session, render_template
from flask_login import UserMixin, current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from config import create_app, db, login_manager

# Create the Flask app
app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import and register blueprints
from controllers.profile_controller import profile_bp
from controllers import (
    auth_controller, book_controller, social_controller, review_controller
)
from controllers.api_controller import api_bp

# Register all blueprints
app.register_blueprint(profile_bp)
app.register_blueprint(api_bp)

# Import models
from models import (
    User, Book, BorrowedBook, Discussion, Notification,
    PrivateMessage, BookReview
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Flask-Login: load user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor
@app.context_processor
def inject_borrowed_count():
    """Inject borrowed count and notification count into all templates"""
    from datetime import datetime, timedelta
    borrowed_count = 0
    notification_count = 0

    if current_user.is_authenticated:
        try:
            current_user.update_activity()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating activity: {e}")

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

# Helper function
def get_user_identifier():
    """Get user ID if logged in, otherwise session ID"""
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    else:
        if "session_id" not in session:
            import uuid
            session["session_id"] = str(uuid.uuid4())
        return f"session_{session['session_id']}"

# Auth routes
@app.route("/login", methods=["GET", "POST"])
def login():
    return auth_controller.login()

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return auth_controller.signup()

@app.route("/logout")
def logout():
    return auth_controller.logout()

# Book routes
@app.route("/")
def index():
    return book_controller.index()

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    return book_controller.book_detail(book_id)

@app.route("/borrow/<int:book_id>", methods=["POST"])
def borrow_book(book_id):
    return book_controller.borrow_book(book_id)

@app.route("/return/<int:book_id>", methods=["POST"])
def return_book(book_id):
    return book_controller.return_book(book_id)

@app.route("/dashboard")
def dashboard():
    return book_controller.dashboard()

@app.route("/post_book", methods=["GET", "POST"])
def post_book():
    return book_controller.post_book()

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    return book_controller.post_book()

@app.route("/seed_books")
def seed_books():
    return book_controller.seed_books()

# ✅ NEW: Book management routes
@app.route("/api/books/<int:book_id>/update_status", methods=["POST"])
def update_book_status(book_id):
    """Toggle book availability status"""
    return book_controller.update_book_status(book_id)

@app.route("/api/books/<int:book_id>/delete", methods=["DELETE", "POST"])
def delete_book(book_id):
    """Delete a book"""
    return book_controller.delete_book(book_id)

# Social routes
@app.route("/discussion", methods=["GET", "POST"])
def discussion():
    return social_controller.discussion()

@app.route("/api/discussion/messages")
def get_discussion_messages():
    return social_controller.get_discussion_messages()

@app.route("/book/<int:book_id>/discussion", methods=["GET", "POST"])
def book_discussion(book_id):
    return social_controller.book_discussion(book_id)

@app.route("/chat/<int:recipient_id>")
@app.route("/chat/<int:recipient_id>/<int:book_id>")
def private_chat(recipient_id, book_id=None):
    return social_controller.private_chat(recipient_id, book_id)

@app.route("/api/chat/<int:recipient_id>/send", methods=["POST"])
def send_private_message(recipient_id):
    return social_controller.send_private_message(recipient_id)

@app.route("/api/chat/<int:recipient_id>/messages")
def get_chat_messages(recipient_id):
    return social_controller.get_chat_messages(recipient_id)

@app.route("/notifications")
def notifications():
    return social_controller.notifications()

@app.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    return social_controller.mark_notification_read(notification_id)

@app.route("/api/notifications/read_all", methods=["POST"])
def mark_all_notifications_read():
    return social_controller.mark_all_notifications_read()

@app.route("/api/notifications/count")
def get_unread_notifications_count():
    return social_controller.get_unread_notifications_count()

@app.route("/notifications/book-request/<int:notification_id>/<action>", methods=["POST"])
def handle_book_request_notification(notification_id, action):
    return social_controller.handle_book_request_notification(notification_id, action)

@app.route("/api/books/<int:book_id>/approve_borrow", methods=["POST"])
def approve_borrow_request(book_id):
    return social_controller.approve_borrow_request(book_id)

@app.route("/api/books/<int:book_id>/reject_borrow", methods=["POST"])
def reject_borrow_request(book_id):
    return social_controller.reject_borrow_request(book_id)

@app.route("/api/books/<int:book_id>/cancel_borrow", methods=["POST"])
def cancel_borrow_request(book_id):
    return social_controller.cancel_borrow_request(book_id)

# Review routes
@app.route("/api/books/<int:book_id>/reviews", methods=["POST"])
def add_review(book_id):
    return review_controller.add_review(book_id)

@app.route("/api/books/<int:book_id>/reviews")
def get_reviews(book_id):
    return review_controller.get_reviews(book_id)

@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    return review_controller.delete_review(review_id)

# Info routes
@app.route("/info")
def info():
    """Display information about ReadingTrail platform"""
    return render_template("info.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

# Setup pytz for templates
import pytz
app.jinja_env.globals['pytz'] = pytz

# Background image
from flask import send_from_directory
import os

@app.route('/background')
def background():
    return send_from_directory(os.getcwd(), 'Background.jpg')

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)