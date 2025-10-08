# Models package
# Import all models to make them available when importing from models
from .user import User
from .book import Book, BorrowedBook
from .social import Discussion, PrivateMessage, Notification
from .review import BookReview
from .achievement import Achievement, UserAchievement, UserProfile
from .powerup import PowerUp, UserPowerUp

# Make all models available at package level
__all__ = [
    'User',
    'Book', 'BorrowedBook',
    'Discussion', 'PrivateMessage', 'Notification',
    'BookReview',
    'Achievement', 'UserAchievement', 'UserProfile',
    'PowerUp', 'UserPowerUp'
]