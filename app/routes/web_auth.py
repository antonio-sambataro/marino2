from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

auth_web_bp = Blueprint('auth_web', __name__)

@auth_web_bp.route('/login')
def login():
    """Render login/registration page."""
    current_year = datetime.now().year
    return render_template('auth.html', current_year=current_year)

@auth_web_bp.route('/logout')
def logout():
    """Handle logout."""
    # Client-side logout is handled by JavaScript
    return redirect(url_for('web.index'))

@auth_web_bp.route('/profile')
@jwt_required()
def profile():
    """Render user profile page."""
    current_year = datetime.now().year
    user_id = get_jwt_identity()
    return render_template('profile.html', current_year=current_year, user_id=user_id)