from flask import Blueprint, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.utils.helpers import admin_required

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@web_bp.route('/menu')
@jwt_required()
def menu():
    current_year = datetime.now().year
    return render_template('menu.html', current_year=current_year)

@web_bp.route('/orders')
@jwt_required()
def orders():
    current_year = datetime.now().year
    return render_template('orders.html', current_year=current_year)

@web_bp.route('/settings')
@jwt_required()
@admin_required
def settings():
    current_year = datetime.now().year
    return render_template('settings.html', current_year=current_year)