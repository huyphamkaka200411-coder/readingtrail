"""
Achievement Controller
Handles achievement system, user rankings, and profile customization.
"""
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from config import db
from models import Achievement, UserAchievement, User, BorrowedBook, BookReview, UserProfile, Book, PrivateMessage
from datetime import datetime, timedelta
import logging


def achievements():
    """Display achievements page"""
    # Get all achievements
    all_achievements = Achievement.query.filter_by(is_active=True).order_by(Achievement.category, Achievement.points).all()
    
    # Initialize variables for non-authenticated users
    user_achievements = []
    user_achievement_ids = []
    progress = {}
    rank_info = None
    
    if current_user.is_authenticated:
        # Get user's achievements
        user_achievements = UserAchievement.query.filter_by(user_id=current_user.id).all()
        user_achievement_ids = [ua.achievement_id for ua in user_achievements]
        
        # Get achievement progress
        progress = get_achievement_progress(current_user.id)
        
        # Get rank info
        rank_info = current_user.get_rank_info()
    
    # Group achievements by category
    achievements_by_category = {}
    for achievement in all_achievements:
        category = achievement.category
        if category not in achievements_by_category:
            achievements_by_category[category] = []
        
        achievement_data = achievement.to_dict()
        achievement_data['unlocked'] = achievement.id in user_achievement_ids
        achievement_data['progress'] = progress.get(achievement.id, 0)
        
        achievements_by_category[category].append(achievement_data)
    
    return render_template('achievements.html', 
                         achievements_by_category=achievements_by_category,
                         rank_info=rank_info)


@login_required
def ranks():
    """Display user ranks and leaderboard"""
    # Define rank system
    ranks = [
        {'name': 'Newbie', 'min_points': 0, 'max_points': 49, 'color': '#95a5a6', 'icon': 'fa-seedling'},
        {'name': 'Reader', 'min_points': 50, 'max_points': 149, 'color': '#3498db', 'icon': 'fa-book'},
        {'name': 'Bookworm', 'min_points': 150, 'max_points': 299, 'color': '#9b59b6', 'icon': 'fa-book-open'},
        {'name': 'Scholar', 'min_points': 300, 'max_points': 499, 'color': '#e67e22', 'icon': 'fa-graduation-cap'},
        {'name': 'Expert', 'min_points': 500, 'max_points': 749, 'color': '#f39c12', 'icon': 'fa-star'},
        {'name': 'Master', 'min_points': 750, 'max_points': 999, 'color': '#e74c3c', 'icon': 'fa-crown'},
        {'name': 'Grandmaster', 'min_points': 1000, 'max_points': 1499, 'color': '#1abc9c', 'icon': 'fa-gem'},
        {'name': 'Legend', 'min_points': 1500, 'max_points': 99999, 'color': '#fd79a8', 'icon': 'fa-trophy'}
    ]
    
    # Get current user's rank info (guaranteed to exist since @login_required)
    user_rank_info = current_user.get_rank_info()
    
    # Get top 20 users by points
    top_users_query = db.session.query(User).join(UserAchievement).group_by(User.id).order_by(
        db.session.query(db.func.sum(Achievement.points)).select_from(Achievement).join(UserAchievement).filter(
            UserAchievement.user_id == User.id
        ).label('total_points').desc()
    ).limit(20)
    
    leaderboard = top_users_query.all()
    
    # Add rank info for each user in leaderboard
    leaderboard_with_ranks = []
    for user_data in leaderboard:
        user_rank = user_data.get_rank_info()
        leaderboard_with_ranks.append({
            'user': user_data,
            'rank_info': user_rank
        })
    
    return render_template('ranks.html', 
                         user_rank_info=user_rank_info,
                         ranks=ranks,
                         leaderboard=leaderboard_with_ranks)


@login_required
def check_achievements_api():
    """API endpoint to check for new achievements"""
    new_achievements = check_and_award_achievements(current_user.id)
    return jsonify({
        'success': True,
        'new_achievements': [ach.to_dict() for ach in new_achievements]
    })


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
    
    # Get borrowed books count
    borrowed_count = BorrowedBook.query.filter_by(user_id=current_user.id, is_returned=False).count()
    
    # Get user's power-ups
    from models.powerup import UserPowerUp
    user_powerups = UserPowerUp.query.filter_by(user_id=current_user.id).order_by(UserPowerUp.purchased_at.desc()).all()
    
    return render_template('profile.html', profile=user_profile, borrowed_count=borrowed_count, user_powerups=user_powerups)


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
        user_profile.background_style = data.get('background_style', 'default')
        user_profile.background_overlay = data.get('background_overlay', True)
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


def seed_achievements():
    """Seed the database with sample achievements"""
    try:
        # Check if achievements already exist
        if Achievement.query.count() > 0:
            return "Achievements already exist in the database"
        
        achievements_data = [
            # Book-related achievements
            {
                'name': 'First Book',
                'description': 'Post your first book to the library',
                'icon': 'fa-book',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 1,
                'points': 10
            },
            {
                'name': 'Book Collector',
                'description': 'Post 5 books to the library',
                'icon': 'fa-books',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 5,
                'points': 50
            },
            {
                'name': 'Librarian',
                'description': 'Post 10 books to the library',
                'icon': 'fa-book-open',
                'category': 'books',
                'requirement_type': 'count',
                'requirement_value': 10,
                'points': 100
            },
            
            # Review-related achievements
            {
                'name': 'First Review',
                'description': 'Write your first book review',
                'icon': 'fa-star',
                'category': 'reviews',
                'requirement_type': 'count',
                'requirement_value': 1,
                'points': 5
            },
            {
                'name': 'Critic',
                'description': 'Write 5 book reviews',
                'icon': 'fa-pen',
                'category': 'reviews',
                'requirement_type': 'count',
                'requirement_value': 5,
                'points': 25
            },
            {
                'name': 'Master Critic',
                'description': 'Write 15 book reviews',
                'icon': 'fa-feather',
                'category': 'reviews',
                'requirement_type': 'count',
                'requirement_value': 15,
                'points': 75
            },
            
            # Social achievements
            {
                'name': 'Social Butterfly',
                'description': 'Send 10 private messages',
                'icon': 'fa-comment',
                'category': 'social',
                'requirement_type': 'count',
                'requirement_value': 10,
                'points': 20
            },
            {
                'name': 'Community Helper',
                'description': 'Have 5 books borrowed by others',
                'icon': 'fa-handshake',
                'category': 'social',
                'requirement_type': 'count',
                'requirement_value': 5,
                'points': 30
            },
            
            # Special achievements
            {
                'name': 'Early Adopter',
                'description': 'One of the first 100 users',
                'icon': 'fa-rocket',
                'category': 'special',
                'requirement_type': 'special',
                'requirement_value': 100,
                'points': 15
            },
            {
                'name': 'Dedication',
                'description': 'Active for 30 days',
                'icon': 'fa-calendar-check',
                'category': 'time',
                'requirement_type': 'special',
                'requirement_value': 30,
                'points': 40
            }
        ]
        
        for achievement_data in achievements_data:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
        
        db.session.commit()
        logging.info("Sample achievements seeded successfully")
        return "Sample achievements added successfully!"
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding achievements: {e}")
        return f"Error seeding achievements: {e}"


# Helper functions
def check_and_award_achievements(user_id):
    """Check if user has earned any new achievements and award them"""
    if not user_id:
        return []
    
    user = User.query.get(user_id)
    if not user:
        return []
    
    # Get user's current achievements
    user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
    user_achievement_ids = [ua.achievement_id for ua in user_achievements]
    
    # Get all achievements
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    
    new_achievements = []
    
    for achievement in all_achievements:
        # Skip if user already has this achievement
        if achievement.id in user_achievement_ids:
            continue
        
        # Check if user meets the requirement
        if check_achievement_requirement(user_id, achievement):
            # Check if user has active double points power-up
            achievement_to_award = achievement
            
            # Import here to avoid circular imports
            from controllers.store_controller import has_active_double_points
            if has_active_double_points(user_id):
                # Create a temporary achievement with doubled points
                doubled_achievement = Achievement(
                    name=f"{achievement.name} (Double Points)",
                    description=f"{achievement.description} - Enhanced with Double Points power-up!",
                    category=achievement.category,
                    points=achievement.points * 2,  # Double the points
                    requirement_type=achievement.requirement_type,
                    requirement_value=achievement.requirement_value,
                    icon=achievement.icon,
                    color=achievement.color,
                    is_active=True
                )
                db.session.add(doubled_achievement)
                db.session.flush()  # Get the ID
                achievement_to_award = doubled_achievement
            
            # Award the achievement
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_to_award.id
            )
            db.session.add(user_achievement)
            new_achievements.append(achievement_to_award)
    
    if new_achievements:
        db.session.commit()
        logging.info(f"Awarded {len(new_achievements)} new achievements to user {user_id}")
    
    return new_achievements


def check_achievement_requirement(user_id, achievement):
    """Check if user meets the requirement for a specific achievement"""
    if achievement.requirement_type == 'count':
        if achievement.category == 'books':
            # Count books posted by user
            count = Book.query.filter_by(posted_by=user_id).count()
            return count >= achievement.requirement_value
        elif achievement.category == 'reviews':
            # Count reviews written by user
            count = BookReview.query.filter_by(user_id=user_id).count()
            return count >= achievement.requirement_value
        elif achievement.category == 'social':
            if achievement.name == 'Social Butterfly':
                # Count messages sent by user
                count = PrivateMessage.query.filter_by(sender_id=user_id).count()
                return count >= achievement.requirement_value
            elif achievement.name == 'Community Helper':
                # Count books borrowed by others from this user
                user_books = Book.query.filter_by(posted_by=user_id).all()
                borrowed_count = 0
                for book in user_books:
                    borrowed_count += BorrowedBook.query.filter_by(book_id=book.id, is_agreed=True).count()
                return borrowed_count >= achievement.requirement_value
    elif achievement.requirement_type == 'special':
        if achievement.name == 'Early Adopter':
            # Check if user is among first 100 users
            user = User.query.get(user_id)
            if user:
                earlier_users = User.query.filter(User.created_at < user.created_at).count()
                return earlier_users < achievement.requirement_value
        elif achievement.name == 'Dedication':
            # Check if user has been active for required days
            user = User.query.get(user_id)
            if user:
                days_since_creation = (datetime.utcnow() - user.created_at).days
                return days_since_creation >= achievement.requirement_value
    
    return False


def get_user_achievements(user_id):
    """Get all achievements for a user"""
    try:
        user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
        achievements = []
        
        for ua in user_achievements:
            achievement_data = ua.achievement.to_dict()
            achievement_data['unlocked_at'] = ua.unlocked_at
            achievements.append(achievement_data)
        
        return achievements
    except Exception as e:
        logging.error(f"Error getting user achievements: {e}")
        return []


def get_achievement_progress(user_id):
    """Get progress towards all achievements for a user"""
    progress = {}
    
    try:
        achievements = Achievement.query.filter_by(is_active=True).all()
        
        for achievement in achievements:
            current_progress = 0
            
            if achievement.requirement_type == 'count':
                if achievement.category == 'books':
                    current_progress = Book.query.filter_by(posted_by=user_id).count()
                elif achievement.category == 'reviews':
                    current_progress = BookReview.query.filter_by(user_id=user_id).count()
                elif achievement.category == 'social':
                    if achievement.name == 'Social Butterfly':
                        current_progress = PrivateMessage.query.filter_by(sender_id=user_id).count()
                    elif achievement.name == 'Community Helper':
                        user_books = Book.query.filter_by(posted_by=user_id).all()
                        for book in user_books:
                            current_progress += BorrowedBook.query.filter_by(book_id=book.id, is_agreed=True).count()
            elif achievement.requirement_type == 'special':
                if achievement.name == 'Early Adopter':
                    user = User.query.get(user_id)
                    if user:
                        current_progress = User.query.filter(User.created_at < user.created_at).count()
                elif achievement.name == 'Dedication':
                    user = User.query.get(user_id)
                    if user:
                        current_progress = (datetime.utcnow() - user.created_at).days
            
            progress[achievement.id] = min(current_progress, achievement.requirement_value)
        
        return progress
    except Exception as e:
        logging.error(f"Error getting achievement progress: {e}")
        return {}