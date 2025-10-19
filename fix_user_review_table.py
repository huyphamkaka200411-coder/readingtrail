from app import app
from config import db
from models.user_review import UserReview

with app.app_context():
    print("⏳ Đang xóa bảng user_reviews (nếu có)...")
    UserReview.__table__.drop(db.engine, checkfirst=True)

    print("🔄 Đang tạo lại tất cả bảng...")
    db.create_all()

    print(
        "✅ Bảng 'user_reviews' đã được tạo lại thành công với cột reviewed_user_id."
    )
