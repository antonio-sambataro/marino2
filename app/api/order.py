from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.order_service import (
    create_order, get_order, get_orders, update_order_status,
    add_payment_to_order, add_item_to_order, remove_item_from_order,
    update_order_item
)
from app.services.printer_service import print_order_to_kitchen
from app.utils.helpers import validate_json

order_bp = Blueprint('order', __name__, url_prefix='/api/orders')

@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_orders():
    """Get all orders with optional filtering."""
    # Get query parameters for filtering
    delivery_type = request.args.get('delivery_type')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    result = get_orders(
        delivery_type=delivery_type,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(result), 200

@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    """Get an order by ID."""
    result = get_order(order_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@order_bp.route('/', methods=['POST'])
@validate_json(['delivery_type'])
def create_new_order():
    """Create a new order."""
    data = request.get_json()
    
    result = create_order(data)
    
    if result['success']:
        # After creating order, send to kitchen printers
        print_order_to_kitchen(result['order_id'])
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@validate_json(['status'])
def update_status(order_id):
    """Update an order's status."""
    data = request.get_json()
    status = data.get('status')
    
    result = update_order_status(order_id, status)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@order_bp.route('/<int:order_id>/items', methods=['POST'])
@validate_json(['product_id', 'qty', 'price'])
def add_item(order_id):
    """Add an item to an order."""
    data = request.get_json()
    
    result = add_item_to_order(order_id, data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@order_bp.route('/<int:order_id>/items/<int:item_id>', methods=['PUT'])
def update_item(order_id, item_id):
    """Update an item in an order."""
    data = request.get_json()
    
    result = update_order_item(order_id, item_id, data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@order_bp.route('/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
def remove_item(order_id, item_id):
    """Remove an item from an order."""
    result = remove_item_from_order(order_id, item_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404

@order_bp.route('/<int:order_id>/payments', methods=['POST'])
@validate_json(['payment_method_id', 'amount'])
def add_payment(order_id):
    """Add a payment to an order."""
    data = request.get_json()
    
    result = add_payment_to_order(order_id, data)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400
