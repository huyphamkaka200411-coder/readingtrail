
from app import app  # import Flask app chính
from config import db

# Import tất cả các model để SQLAlchemy nhận diện bảng
from models.user import User
from models.book import Book, BorrowedBook
from models.review import BookReview
from models.user_review import UserReview
from models.social import Follow

# Nếu bạn có model khác thì import thêm ở đây nhé 👇
# from models.xxx import XxxModel


if __name__ == "__main__":
    with app.app_context():
        print("🔄 Đang tạo cơ sở dữ liệu và các bảng...")
        db.create_all()
        print("✅ Tạo bảng thành công!")
