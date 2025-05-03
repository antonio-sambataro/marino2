from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import jwt_required
from datetime import datetime

menu_web_bp = Blueprint('menu_web', __name__, url_prefix='/menu')

@menu_web_bp.route('/')
def index():
    """Render menu dashboard."""
    current_year = datetime.now().year
    return render_template('menu/index.html', current_year=current_year)

@menu_web_bp.route('/categories')
@jwt_required()
def categories():
    """Render categories management page."""
    current_year = datetime.now().year
    return render_template('categories.html', current_year=current_year)

@menu_web_bp.route('/products')
@jwt_required()
def products():
    """Render products management page."""
    current_year = datetime.now().year
    return render_template('products.html', current_year=current_year)

@menu_web_bp.route('/price-lists')
@jwt_required()
def price_lists():
    """Render price lists management page."""
    current_year = datetime.now().year
    return render_template('menu/price_lists.html', current_year=current_year)

@menu_web_bp.route('/variants')
@jwt_required()
def variants():
    """Render variant categories management page."""
    current_year = datetime.now().year
    return render_template('menu/variants.html', current_year=current_year)