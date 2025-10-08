"""
Store Controller
Handles power-up store functionality, purchases, and activation.
"""
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from config import db
from models import User, UserAchievement, Achievement
from models.powerup import PowerUp, UserPowerUp
from datetime import datetime, timedelta
import logging
import random


@login_required
def store():
    """Display store page with available power-ups - requires Bookworm rank"""

    # Check if user has at least Bookworm rank (150+ points)
    user_points = current_user.get_total_points()
    rank_info = current_user.get_rank_info()

    # Bookworm rank requires 150+ points
    if user_points < 150:
        flash(
            f'You need at least the "Bookworm" rank (150 points) to access the store. You currently have {user_points} points.',
            'warning')
        return redirect(url_for('achievements'))

    # Get all available power-ups
    available_powerups = PowerUp.query.filter_by(is_active=True).order_by(
        PowerUp.cost).all()

    # Get user's purchased power-ups
    user_powerups = UserPowerUp.query.filter_by(user_id=current_user.id).all()

    return render_template('store.html',
                           powerups=available_powerups,
                           user_points=user_points,
                           user_powerups=user_powerups,
                           rank_info=rank_info)


@login_required
def purchase_powerup():
    """Handle power-up purchase"""
    try:
        data = request.get_json()
        powerup_id = data.get('powerup_id')

        if not powerup_id:
            return jsonify({
                'success': False,
                'message': 'Invalid power-up selection'
            }), 400

        # Get the power-up
        powerup = PowerUp.query.get(powerup_id)
        if not powerup or not powerup.is_active:
            return jsonify({
                'success': False,
                'message': 'Power-up not found or unavailable'
            }), 404

        # Special handling for Leech: cancel any existing active leech
        cancelled_existing_leech = False
        if powerup.powerup_type == 'leech':
            existing_leech = UserPowerUp.query.join(PowerUp).filter(
                UserPowerUp.user_id == current_user.id,
                PowerUp.powerup_type == 'leech', UserPowerUp.is_active == True,
                UserPowerUp.expires_at > datetime.utcnow()).first()

            if existing_leech:
                # Deactivate the existing leech
                existing_leech.is_active = False
                existing_leech.expires_at = datetime.utcnow()  # Set to expired
                cancelled_existing_leech = True
                logging.info(
                    f"Cancelled existing active leech for user {current_user.id}"
                )

        # Check for other power-up types (prevent duplicates for non-leech power-ups)
        elif powerup.powerup_type != 'leech':
            existing_powerup = UserPowerUp.query.join(PowerUp).filter(
                UserPowerUp.user_id == current_user.id,
                PowerUp.powerup_type == powerup.powerup_type).first()

            if existing_powerup:
                return jsonify({
                    'success':
                    False,
                    'message':
                    f'You already own a {powerup.name} power-up! You can only have one of each type.'
                }), 400

        # Check if user has enough points
        user_points = current_user.get_total_points()
        if powerup.cost > user_points:
            return jsonify({
                'success':
                False,
                'message':
                f'Not enough points! You need {powerup.cost} points but only have {user_points}.'
            }), 400

        # Create a unique achievement to deduct points
        # Add timestamp to make achievement names unique
        purchase_time = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        deduction_achievement = Achievement(
            name=f"Purchased {powerup.name} - {purchase_time}",
            description=f"Points spent on {powerup.name}",
            category="store",
            points=-powerup.cost,  # Negative points to deduct
            requirement_type="purchase",
            requirement_value=1,
            icon="fa-shopping-cart",
            color="#e74c3c")
        db.session.add(deduction_achievement)
        db.session.flush()  # Get the ID

        # Add user achievement for the deduction
        user_achievement = UserAchievement(
            user_id=current_user.id,
            achievement_id=deduction_achievement.id,
            unlocked_at=datetime.utcnow())
        db.session.add(user_achievement)

        # Create user power-up
        user_powerup = UserPowerUp(user_id=current_user.id,
                                   powerup_id=powerup.id,
                                   purchased_at=datetime.utcnow())
        db.session.add(user_powerup)

        db.session.commit()

        # Calculate remaining points
        remaining_points = user_points - powerup.cost

        # Create success message with cancellation info if applicable
        success_message = f'Successfully purchased {powerup.name} for {powerup.cost} points!'
        if cancelled_existing_leech:
            success_message += ' Your previous leech has been cancelled and replaced.'

        flash(success_message, 'success')
        logging.info(
            f"User {current_user.id} purchased power-up {powerup.name} for {powerup.cost} points"
        )

        return jsonify({
            'success':
            True,
            'message':
            f'Successfully purchased {powerup.name}!' +
            (' Previous leech cancelled.' if cancelled_existing_leech else ''),
            'remaining_points':
            remaining_points,
            'powerup':
            powerup.to_dict()
        })

    except Exception as e:
        logging.error(f"Error purchasing power-up: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to purchase power-up'
        }), 500


@login_required
def activate_powerup():
    """Activate a purchased power-up"""
    try:
        data = request.get_json()
        user_powerup_id = data.get('user_powerup_id')

        if not user_powerup_id:
            return jsonify({
                'success': False,
                'message': 'Invalid power-up selection'
            }), 400

        # Get the user power-up
        user_powerup = UserPowerUp.query.filter_by(
            id=user_powerup_id, user_id=current_user.id).first()

        if not user_powerup:
            return jsonify({
                'success': False,
                'message': 'Power-up not found'
            }), 404

        # Check if already consumed or active
        if user_powerup.is_consumed:
            return jsonify({
                'success': False,
                'message': 'This power-up has already been used'
            }), 400

        if user_powerup.is_active and not user_powerup.is_expired():
            return jsonify({
                'success': False,
                'message': 'This power-up is already active'
            }), 400

        # Activate the power-up
        success = user_powerup.activate()
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to activate power-up'
            }), 400

        # Handle specific power-up logic
        message = f'{user_powerup.powerup.name} activated!'

        if user_powerup.powerup.powerup_type == 'leech':
            # Execute leech logic - find target from top 10 users
            target_user = find_leech_target(user_powerup)
            if target_user:
                message = f'Leech activated! You are now leeching points from {target_user.get_full_name()} ({target_user.username}), one of the top 10 offline users. You will gain 5-6% of their points every 5 minutes for the next 24 hours.'
            else:
                message = 'Leech activated, but no suitable offline targets found in the top 10 users.'

        elif user_powerup.powerup.powerup_type == 'double_points':
            message = f'Double Points activated! Your point earnings are doubled for {user_powerup.powerup.duration_hours} hours.'

        db.session.commit()

        flash(message, 'success')
        logging.info(
            f"User {current_user.id} activated power-up {user_powerup.powerup.name}"
        )

        return jsonify({
            'success': True,
            'message': message,
            'user_powerup': user_powerup.to_dict()
        })

    except Exception as e:
        logging.error(f"Error activating power-up: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to activate power-up'
        }), 500


def find_leech_target(user_powerup):
    """Find a target from top 10 users for leech power-up"""
    try:
        # Get top 10 users by points, excluding current user
        top_users_query = db.session.query(User).join(
            UserAchievement).group_by(User.id).order_by(
                db.session.query(db.func.sum(Achievement.points)).select_from(
                    Achievement).join(UserAchievement).filter(
                        UserAchievement.user_id == User.id).label(
                            'total_points').desc()).filter(
                                User.id != current_user.id).limit(10).all()

        # Filter users who have enough points and are offline
        viable_targets = []
        for user in top_users_query:
            user_points = user.get_total_points()
            if user_points >= 100 and not user.is_online(
            ):  # Minimum points and must be offline
                viable_targets.append(user)

        if not viable_targets:
            return None

        # Select random target from top users
        target_user = random.choice(viable_targets)

        # Set the target in the user_powerup
        user_powerup.leeched_user_id = target_user.id
        user_powerup.leeched_points = 0  # Will accumulate over time

        logging.info(
            f"Leech target selected: User {current_user.id} will leech from User {target_user.id} ({target_user.username})"
        )

        return target_user

    except Exception as e:
        logging.error(f"Error finding leech target: {e}")
        return None


def process_active_leeches():
    """Process all active leech power-ups to award points every 5 minutes"""
    try:
        # Find all active leech power-ups
        active_leeches = UserPowerUp.query.filter_by(
            is_active=True).join(PowerUp).filter(
                PowerUp.powerup_type == 'leech', UserPowerUp.expires_at
                > datetime.utcnow()).all()

        for leech in active_leeches:
            if leech.leeched_user_id:
                target_user = User.query.get(leech.leeched_user_id)

                # Check if target is still offline
                if target_user and not target_user.is_online():
                    # Award 5-6% of target's current points
                    target_points = target_user.get_total_points()
                    leech_percentage = random.uniform(0.05, 0.06)  # 5-6%
                    points_to_award = max(
                        1, int(target_points *
                               leech_percentage))  # Minimum 1 point

                    # Create achievement for points gained
                    leech_gain = Achievement(
                        description=
                        f"Points leeched from {target_user.username} ({points_to_award} pts)",
                        category="store",
                        points=points_to_award,
                        requirement_type="leech_5min",
                        requirement_value=1,
                        icon="fa-vampire-teeth",
                        color="#32cd32")
                    db.session.add(leech_gain)
                    db.session.flush()

                    user_achievement = UserAchievement(
                        user_id=leech.user_id,
                        achievement_id=leech_gain.id,
                        unlocked_at=datetime.utcnow())
                    db.session.add(user_achievement)

                    # Update total leeched points
                    leech.leeched_points += points_to_award

                    logging.info(
                        f"Leech 5min: User {leech.user_id} gained {points_to_award} points ({leech_percentage:.1%}) from offline User {leech.leeched_user_id}"
                    )
                else:
                    logging.info(
                        f"Leech paused: Target User {leech.leeched_user_id} is online"
                    )

        db.session.commit()

    except Exception as e:
        logging.error(f"Error processing active leeches: {e}")
        db.session.rollback()


def seed_powerups():
    """Seed initial power-ups"""
    try:
        # Check if power-ups already exist
        existing_powerups = PowerUp.query.count()
        if existing_powerups > 0:
            flash('Power-ups already exist!', 'info')
            return redirect(url_for('store'))

        # Create initial power-ups
        powerups = [
            {
                'name': 'Leech',
                'description':
                'Leech 5-6% of points from a random top 10 offline user every 5 minutes for 24 hours. Only works when target is offline.',
                'cost': 600,
                'powerup_type': 'leech',
                'duration_hours': 24,
                'effect_value': 0.055,  # 5.5% average
                'icon': 'fa-vampire-teeth',
                'color': '#8b0000'
            },
            {
                'name': 'Double Points',
                'description':
                'Double your point earnings from all activities for 5 hours.',
                'cost': 200,
                'powerup_type': 'double_points',
                'duration_hours': 5,
                'effect_value': 2.0,
                'icon': 'fa-gem',
                'color': '#ffd700'
            }
        ]

        for powerup_data in powerups:
            powerup = PowerUp(**powerup_data)
            db.session.add(powerup)

        db.session.commit()

        flash('Power-ups seeded successfully!', 'success')
        logging.info("Power-ups seeded successfully")

        return redirect(url_for('store'))

    except Exception as e:
        logging.error(f"Error seeding power-ups: {e}")
        db.session.rollback()
        flash('Failed to seed power-ups', 'error')
        return redirect(url_for('store'))


def get_user_active_powerups(user_id):
    """Get user's currently active power-ups"""
    active_powerups = UserPowerUp.query.filter_by(
        user_id=user_id, is_active=True).join(PowerUp).filter(
            db.or_(
                PowerUp.duration_hours.is_(None),  # Permanent effects
                UserPowerUp.expires_at > datetime.utcnow()  # Not expired
            )).all()

    return active_powerups


def has_active_double_points(user_id):
    """Check if user has active double points power-up"""
    active_double_points = UserPowerUp.query.filter_by(
        user_id=user_id, is_active=True).join(PowerUp).filter(
            PowerUp.powerup_type == 'double_points', UserPowerUp.expires_at
            > datetime.utcnow()).first()

    return active_double_points is not None
