"""
Review Controller
Handles book reviews and ratings functionality.
"""
from flask import request, jsonify
from flask_login import login_required, current_user
from config import db
from models import BookReview, Book
from datetime import datetime
import logging


@login_required
def add_review(book_id):
    """Add or update a review for a book"""
    try:
        data = request.get_json()
        rating = int(data.get('rating'))
        review_text = data.get('review_text', '').strip()
        
        if not 1 <= rating <= 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400
        
        # Check if book exists
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        # Check if user already has a review for this book
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
            review = BookReview()
            review.book_id = book_id
            review.user_id = current_user.id
            review.rating = rating
            review.review_text = review_text
            db.session.add(review)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review saved successfully'
        })
        
    except Exception as e:
        logging.error(f"Error saving review: {e}")
        return jsonify({'success': False, 'error': 'Failed to save review'}), 500


def get_reviews(book_id):
    """Get all reviews for a book"""
    try:
        reviews = BookReview.query.filter_by(book_id=book_id).order_by(BookReview.created_at.desc()).all()
        
        reviews_data = []
        for review in reviews:
            reviews_data.append(review.to_dict())
        
        return jsonify({
            'success': True,
            'reviews': reviews_data
        })
        
    except Exception as e:
        logging.error(f"Error fetching reviews: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch reviews'}), 500


@login_required
def delete_review(review_id):
    """Delete a review (only by the author)"""
    try:
        review = BookReview.query.get(review_id)
        
        if not review:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        # Check if current user is the author of the review
        if review.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        db.session.delete(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting review: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete review'}), 500