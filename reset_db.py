from app import app
from config import db

with app.app_context():
    db.session.rollback()
    print("✅ Transaction reset successfully")

    with db.engine.connect() as conn:
        conn.execute(db.text("ALTER TABLE books ADD COLUMN IF NOT EXISTS location VARCHAR(100) DEFAULT 'Không xác định';"))
        conn.execute(db.text("ALTER TABLE books DROP COLUMN IF EXISTS isbn;"))
        conn.commit()

    print("✅ Done! Added 'location' column and removed 'isbn'")
