import cloudinary
import cloudinary.uploader
import os
from PIL import Image
from io import BytesIO

# Cấu hình Cloudinary - ĐÚNG
cloudinary.config(
    cloud_name='dufihcma4',
    api_key='153926519663158',
    api_secret='i4xKhWonEgeXQ9XyE9axYYBKeGk'
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Kiểm tra file có phải ảnh hợp lệ không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_book_cover(file):
    """
    Upload ảnh bìa sách lên Cloudinary
    Returns: URL của ảnh hoặc None nếu lỗi
    """
    try:
        # Kiểm tra file tồn tại
        if not file or file.filename == '':
            return None

        # Kiểm tra định dạng file
        if not allowed_file(file.filename):
            raise ValueError("Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP")

        # Kiểm tra kích thước file
        file.seek(0, 2)  # Di chuyển con trỏ đến cuối file
        file_size = file.tell()
        file.seek(0)  # Quay lại đầu file

        if file_size > MAX_FILE_SIZE:
            raise ValueError("File quá lớn. Tối đa 5MB")

        # Upload lên Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder="readingtrail/book_covers",
            transformation=[
                {'width': 800, 'height': 1200, 'crop': 'limit'},
                {'quality': 'auto:good'}
            ],
            resource_type="image"
        )

        # Trả về URL an toàn (HTTPS)
        return result['secure_url']

    except ValueError as e:
        print(f"Validation error: {e}")
        raise e
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None