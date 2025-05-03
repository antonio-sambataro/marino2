from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.menu_service import (
    get_categories, get_products, get_price_lists, get_variant_categories,
    create_category, create_product, create_price_list, create_variant_category,
    update_category, update_product, update_price_list, update_variant_category,
    delete_category, delete_product, delete_price_list, delete_variant_category
)
from app.utils.helpers import validate_json, admin_required

menu_bp = Blueprint('menu', __name__, url_prefix='/api/menu')

# Category routes
@menu_bp.route('/categories', methods=['GET'])
def get_all_categories():
    """Get all categories."""
    result = get_categories()
    return jsonify(result), 200

@menu_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get a category by ID."""
    result = get_categories(category_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/categories', methods=['POST'])
@jwt_required()
@admin_required
@validate_json(['name'])
def create_new_category():
    """Create a new category."""
    data = request.get_json()
    name = data.get('name')
    shop_id = data.get('shop_id')
    
    result = create_category(name, shop_id)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@menu_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json(['name'])
def update_existing_category(category_id):
    """Update a category."""
    data = request.get_json()
    name = data.get('name')
    shop_id = data.get('shop_id')
    
    result = update_category(category_id, name, shop_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_existing_category(category_id):
    """Delete a category."""
    result = delete_category(category_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

# Product routes
@menu_bp.route('/products', methods=['GET'])
def get_all_products():
    """Get all products."""
    category_id = request.args.get('category_id', type=int)
    price_list_id = request.args.get('price_list_id', type=int)
    
    result = get_products(category_id=category_id, price_list_id=price_list_id)
    return jsonify(result), 200

@menu_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a product by ID."""
    result = get_products(product_id=product_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/products', methods=['POST'])
@jwt_required()
@admin_required
@validate_json(['name'])
def create_new_product():
    """Create a new product."""
    data = request.get_json()
    
    result = create_product(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@menu_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_existing_product(product_id):
    """Update a product."""
    data = request.get_json()
    
    result = update_product(product_id, data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_existing_product(product_id):
    """Delete a product."""
    result = delete_product(product_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

# Price list routes
@menu_bp.route('/price-lists', methods=['GET'])
def get_all_price_lists():
    """Get all price lists."""
    result = get_price_lists()
    return jsonify(result), 200

@menu_bp.route('/price-lists/<int:price_list_id>', methods=['GET'])
def get_price_list(price_list_id):
    """Get a price list by ID."""
    result = get_price_lists(price_list_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/price-lists', methods=['POST'])
@jwt_required()
@admin_required
@validate_json(['name'])
def create_new_price_list():
    """Create a new price list."""
    data = request.get_json()
    name = data.get('name')
    
    result = create_price_list(name)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@menu_bp.route('/price-lists/<int:price_list_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json(['name'])
def update_existing_price_list(price_list_id):
    """Update a price list."""
    data = request.get_json()
    name = data.get('name')
    
    result = update_price_list(price_list_id, name)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/price-lists/<int:price_list_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_existing_price_list(price_list_id):
    """Delete a price list."""
    result = delete_price_list(price_list_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

# Variant category routes
@menu_bp.route('/variant-categories', methods=['GET'])
def get_all_variant_categories():
    """Get all variant categories."""
    result = get_variant_categories()
    return jsonify(result), 200

@menu_bp.route('/variant-categories/<int:variant_category_id>', methods=['GET'])
def get_variant_category(variant_category_id):
    """Get a variant category by ID."""
    result = get_variant_categories(variant_category_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/variant-categories', methods=['POST'])
@jwt_required()
@admin_required
@validate_json(['name'])
def create_new_variant_category():
    """Create a new variant category."""
    data = request.get_json()
    
    result = create_variant_category(data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@menu_bp.route('/variant-categories/<int:variant_category_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_existing_variant_category(variant_category_id):
    """Update a variant category."""
    data = request.get_json()
    
    result = update_variant_category(variant_category_id, data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@menu_bp.route('/variant-categories/<int:variant_category_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_existing_variant_category(variant_category_id):
    """Delete a variant category."""
    result = delete_variant_category(variant_category_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404
