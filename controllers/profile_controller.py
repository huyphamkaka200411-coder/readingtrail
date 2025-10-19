from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from config import db
from models.user import User
from models.user_review import UserReview

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.description = request.form.get("description", "").strip()
        current_user.first_name = request.form.get("first_name", "").strip()
        current_user.last_name = request.form.get("last_name", "").strip()

        try:
            db.session.commit()
            flash("Cập nhật hồ sơ thành công!", "success")
        except Exception:
            db.session.rollback()
            flash("Có lỗi khi lưu hồ sơ.", "danger")

        return redirect(url_for("profile.profile"))

    return render_template("profile.html", user=current_user)


@profile_bp.route("/<int:user_id>")
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.is_authenticated and current_user.id == user.id:
        return redirect(url_for("profile.profile"))
    return render_template("view_profile.html", user=user)


@profile_bp.route("/<int:user_id>/reviews")
def user_reviews(user_id):
    user = User.query.get_or_404(user_id)
    reviews = (
        UserReview.query
        .filter_by(reviewed_user_id=user.id)
        .order_by(UserReview.updated_at.desc())
        .all()
    )
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render_template("user_reviews.html", user=user, reviews=reviews, avg_rating=avg_rating)


@profile_bp.route("/<int:user_id>/review", methods=["GET", "POST"])
@login_required
def review_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.id == user.id:
        flash("Bạn không thể tự đánh giá chính mình.", "warning")
        return redirect(url_for("profile.view_profile", user_id=user.id))

    existing_review = UserReview.query.filter_by(
        reviewer_id=current_user.id,
        reviewed_user_id=user.id
    ).first()

    if request.method == "POST":
        rating = request.form.get("rating", type=int)
        comment = request.form.get("comment", "").strip()

        if not rating or rating < 1 or rating > 10:
            flash("Điểm đánh giá phải từ 1 đến 10.", "danger")
            return redirect(url_for("profile.review_user", user_id=user.id))

        try:
            if existing_review:
                existing_review.rating = rating
                existing_review.comment = comment
                existing_review.updated_at = datetime.utcnow()
                msg = "Cập nhật đánh giá thành công!"
            else:
                new_review = UserReview(
                    reviewer_id=current_user.id,
                    reviewed_user_id=user.id,
                    rating=rating,
                    comment=comment,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_review)
                msg = "Đánh giá đã được gửi!"

            db.session.commit()
            flash(msg, "success")
        except Exception as e:
            db.session.rollback()
            flash("Có lỗi xảy ra khi lưu đánh giá.", "danger")

        return redirect(url_for("profile.user_reviews", user_id=user.id))

    return render_template("review_user.html", target_user=user, existing_review=existing_review)