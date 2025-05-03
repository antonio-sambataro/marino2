from flask import Blueprint, render_template, redirect, url_for
from datetime import datetime

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@web_bp.route('/menu')
def menu():
    current_year = datetime.now().year
    return render_template('menu.html', current_year=current_year)

@web_bp.route('/orders')
def orders():
    current_year = datetime.now().year
    return render_template('orders.html', current_year=current_year)

@web_bp.route('/settings')
def settings():
    current_year = datetime.now().year
    return render_template('settings.html', current_year=current_year)