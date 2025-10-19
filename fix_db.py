from app import app
from config import db
from models.user_review import UserReview

with app.app_context():
    for r in UserReview.query.all():
        print(r.id, r.reviewer_id, r.reviewed_user_id, r.rating, repr(r.comment))
