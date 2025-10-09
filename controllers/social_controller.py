"""
Social Controller
Handles social features like discussions, private messages, and user profiles.
"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from config import db
from models import Discussion, PrivateMessage, User, Book, Notification, BorrowedBook
from datetime import datetime
import logging


def discussion():
    """Discussion/chat page"""
    if request.method == 'POST':
        message_text = request.form.get('message')
        username = request.form.get('username', 'Anonymous')
        
        if message_text and message_text.strip():
            try:
                # Create new discussion message
                discussion_msg = Discussion()
                discussion_msg.user_id = current_user.id if current_user.is_authenticated else None
                discussion_msg.username = current_user.username if current_user.is_authenticated else username
                discussion_msg.message = message_text.strip()
                discussion_msg.book_id = None  # General discussion, not book-specific
                
                db.session.add(discussion_msg)
                db.session.commit()
                
                flash('Message posted successfully!', 'success')
            except Exception as e:
                logging.error(f"Error posting discussion message: {e}")
                flash('Failed to post message', 'error')
        else:
            flash('Please enter a message', 'error')
        
        return redirect(url_for('discussion'))
    
    # GET request - show discussion page
    return render_template('discussion.html')


def get_discussion_messages():
    """API endpoint to get discussion messages for real-time updates"""
    try:
        messages = Discussion.query.filter_by(book_id=None).order_by(Discussion.created_at.desc()).limit(50).all()
        messages_data = []
        for msg in messages:
            messages_data.append(msg.to_dict())
        
        return jsonify({
            'success': True,
            'messages': list(reversed(messages_data))
        })
    except Exception as e:
        logging.error(f"Error fetching discussion messages: {e}")
        return jsonify({'success': False, 'error': str(e)})


def book_discussion(book_id):
    """Book-specific discussion page"""
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        message_text = request.form.get('message')
        username = request.form.get('username', 'Anonymous')
        
        if message_text and message_text.strip():
            try:
                # Create new book discussion message
                discussion_msg = Discussion()
                discussion_msg.user_id = current_user.id if current_user.is_authenticated else None
                discussion_msg.username = current_user.username if current_user.is_authenticated else username
                discussion_msg.message = message_text.strip()
                discussion_msg.book_id = book_id
                
                db.session.add(discussion_msg)
                db.session.commit()
                
                flash('Message posted successfully!', 'success')
            except Exception as e:
                logging.error(f"Error posting book discussion message: {e}")
                flash('Failed to post message', 'error')
        else:
            flash('Please enter a message', 'error')
        
        return redirect(url_for('book_discussion', book_id=book_id))
    
    # GET request - show book discussion page
    try:
        # Fetch messages for this book
        messages = Discussion.query.filter_by(book_id=book_id).order_by(Discussion.created_at.asc()).all()
        
        # Add Vietnam timezone formatting for each message
        for message in messages:
            if message.created_at:
                from pytz import timezone
                vn_tz = timezone('Asia/Ho_Chi_Minh')
                local_time = message.created_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
                message.vietnam_time = local_time.strftime('%d/%m/%Y %H:%M')
            else:
                message.vietnam_time = 'Unknown time'
        
        return render_template('book_discussion.html', book=book, messages=messages)
    except Exception as e:
        logging.error(f"Error loading book discussion messages: {e}")
        return render_template('book_discussion.html', book=book, messages=[])


def private_chat(recipient_id, book_id=None):
    """Private chat page with another user, optionally about a specific book"""
    if not current_user.is_authenticated:
        flash('Please login to access private chat', 'error')
        return redirect(url_for('login'))
    
    recipient = User.query.get_or_404(recipient_id)
    
    # Get book context if provided
    book = None
    if book_id:
        book = Book.query.get(book_id)
    
    # Get existing messages between users
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == recipient_id)) |
        ((PrivateMessage.sender_id == recipient_id) & (PrivateMessage.recipient_id == current_user.id))
    ).order_by(PrivateMessage.timestamp.asc()).all()
    
    # Add time_ago field for template compatibility
    for message in messages:
        from pytz import timezone
        import datetime
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = message.timestamp.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
        
        # Calculate time ago
        now = datetime.datetime.utcnow().replace(tzinfo=timezone('UTC'))
        time_diff = now - message.timestamp.replace(tzinfo=timezone('UTC'))
        
        if time_diff.days > 0:
            message.time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            message.time_ago = f"{time_diff.seconds // 3600}h ago"
        elif time_diff.seconds > 60:
            message.time_ago = f"{time_diff.seconds // 60}m ago"
        else:
            message.time_ago = "just now"
    
    # Mark messages as read
    PrivateMessage.query.filter_by(
        sender_id=recipient_id,
        recipient_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template('private_chat.html', 
                         recipient=recipient, 
                         book=book,
                         messages=messages)


def send_private_message(recipient_id):
    """Send a private message"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        message_text = data.get('message', '').strip()
        book_id = data.get('book_id')
        
        if not message_text:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        # Create message
        message = PrivateMessage()
        message.sender_id = current_user.id
        message.recipient_id = recipient_id
        message.message = message_text
        message.book_id = book_id if book_id else None
        
        db.session.add(message)
        
        # Create notification for the recipient
        if book_id:
            book = Book.query.get(book_id)
            notification_message = f'{current_user.get_full_name() or current_user.username} wants to talk with you about "{book.title}"'
            notification_title = 'New Message About Your Book'
        else:
            notification_message = f'{current_user.get_full_name() or current_user.username} sent you a private message'
            notification_title = 'New Private Message'
        
        notification = Notification()
        notification.user_id = recipient_id
        notification.type = 'private_message'
        notification.title = notification_title
        notification.message = notification_message
        notification.book_id = book_id if book_id else None
        notification.related_user_id = current_user.id
        
        db.session.add(notification)
        db.session.commit()
        
        logging.info(f"Private message sent from {current_user.id} to {recipient_id}, notification created")
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error sending private message: {e}")
        return jsonify({'success': False, 'error': 'Failed to send message'}), 500


def get_chat_messages(recipient_id):
    """Get chat messages for real-time updates"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get messages between current user and recipient
        messages = PrivateMessage.query.filter(
            ((PrivateMessage.sender_id == current_user.id) & (PrivateMessage.recipient_id == recipient_id)) |
            ((PrivateMessage.sender_id == recipient_id) & (PrivateMessage.recipient_id == current_user.id))
        ).order_by(PrivateMessage.timestamp.asc()).all()
        
        messages_data = []
        for msg in messages:
            messages_data.append(msg.to_dict())
        
        return jsonify({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        logging.error(f"Error fetching chat messages: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch messages'}), 500


def notifications():
    """Notifications page"""
    if not current_user.is_authenticated:
        flash('Please login to view notifications', 'error')
        return redirect(url_for('login'))
    
    # Get all notifications for current user
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=user_notifications)


def mark_notification_read(notification_id):
    """Mark a notification as read"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark notification'}), 500


def mark_all_notifications_read():
    """Mark all notifications as read"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark notifications'}), 500


def get_unread_notifications_count():
    """Get count of unread notifications"""
    if not current_user.is_authenticated:
        return jsonify({'count': 0})
    
    try:
        count = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({'count': count})
        
    except Exception as e:
        logging.error(f"Error getting notification count: {e}")
        return jsonify({'count': 0})


def handle_book_request_notification(notification_id, action):
    """Handle accept/decline actions for book request notifications"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get the notification
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user.id,
            type='borrow_request'
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
        
        # Get the related borrow request
        from models.book import BorrowedBook
        borrow_request = BorrowedBook.query.filter_by(
            book_id=notification.book_id,
            user_id=notification.related_user_id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_request:
            return jsonify({'success': False, 'error': 'Borrow request not found'}), 404
        
        book = Book.query.get(notification.book_id)
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        if action == 'accept':
            # Accept the request
            borrow_request.is_agreed = True
            borrow_request.agreed_due_date = borrow_request.due_date
            book.available = False
            
            # Create notification for borrower
            borrower_notification = Notification()
            borrower_notification.user_id = notification.related_user_id
            borrower_notification.type = 'borrow_approved'
            borrower_notification.title = 'Book Request Approved'
            borrower_notification.message = f'Your request to borrow "{book.title}" has been approved!'
            borrower_notification.book_id = book.id
            borrower_notification.related_user_id = current_user.id
            db.session.add(borrower_notification)
            
            logging.info(f"Book request approved for book {book.id} by user {current_user.id}")
            
        elif action == 'decline':
            # Decline the request - remove the borrow request
            db.session.delete(borrow_request)
            
            # Create notification for borrower
            borrower_notification = Notification()
            borrower_notification.user_id = notification.related_user_id
            borrower_notification.type = 'borrow_declined'
            borrower_notification.title = 'Book Request Declined'
            borrower_notification.message = f'Your request to borrow "{book.title}" has been declined.'
            borrower_notification.book_id = book.id
            borrower_notification.related_user_id = current_user.id
            db.session.add(borrower_notification)
            
            logging.info(f"Book request declined for book {book.id} by user {current_user.id}")
        
        # Mark the original notification as read
        notification.is_read = True
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Request {action}ed successfully'
        })
        
    except Exception as e:
        logging.error(f"Error handling book request notification: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to process request'}), 500


def approve_borrow_request(book_id):
    """Approve a borrow request with agreed due date"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        agreed_due_date = data.get('agreed_due_date')
        borrower_id = data.get('borrower_id')
        
        if not agreed_due_date or not borrower_id:
            return jsonify({'success': False, 'error': 'Missing required data'}), 400
        
        # Parse the date
        try:
            agreed_due_date = datetime.strptime(agreed_due_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        # Find the borrow request
        borrow_request = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=borrower_id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_request:
            return jsonify({'success': False, 'error': 'Borrow request not found'}), 404
        
        # Check if current user owns the book
        book = Book.query.get(book_id)
        if not book or book.posted_by != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Approve the request
        borrow_request.is_agreed = True
        borrow_request.agreed_due_date = agreed_due_date
        
        # Update book availability
        book.available = False
        
        db.session.commit()
        
        logging.info(f"Borrow request approved for book {book_id} by user {current_user.id}")
        
        return jsonify({'success': True, 'message': 'Borrow request approved successfully'})
        
    except Exception as e:
        logging.error(f"Error approving borrow request: {e}")
        return jsonify({'success': False, 'error': 'Failed to approve request'}), 500


def reject_borrow_request(book_id):
    """Reject a borrow request"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        borrower_id = data.get('borrower_id')
        
        if not borrower_id:
            return jsonify({'success': False, 'error': 'Missing borrower ID'}), 400
        
        # Find the borrow request
        borrow_request = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=borrower_id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_request:
            return jsonify({'success': False, 'error': 'Borrow request not found'}), 404
        
        # Check if current user owns the book
        book = Book.query.get(book_id)
        if not book or book.posted_by != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete the request
        db.session.delete(borrow_request)
        db.session.commit()
        
        logging.info(f"Borrow request rejected for book {book_id} by user {current_user.id}")
        
        return jsonify({'success': True, 'message': 'Borrow request rejected'})
        
    except Exception as e:
        logging.error(f"Error rejecting borrow request: {e}")
        return jsonify({'success': False, 'error': 'Failed to reject request'}), 500


def cancel_borrow_request(book_id):
    """Cancel user's own borrow request"""
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Find the borrow request
        borrow_request = BorrowedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False,
            is_agreed=False
        ).first()
        
        if not borrow_request:
            return jsonify({'success': False, 'error': 'Borrow request not found'}), 404
        
        # Delete the request
        db.session.delete(borrow_request)
        db.session.commit()
        
        logging.info(f"Borrow request cancelled for book {book_id} by user {current_user.id}")
        
        return jsonify({'success': True, 'message': 'Borrow request cancelled'})
        
    except Exception as e:
        logging.error(f"Error cancelling borrow request: {e}")
        return jsonify({'success': False, 'error': 'Failed to cancel request'}), 500