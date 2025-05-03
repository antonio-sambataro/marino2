from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.auth_service import authenticate_user, create_user, get_user
from app.utils.helpers import validate_json

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@validate_json(['username', 'password'])
def login():
    """Log in a user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    result = authenticate_user(username, password)
    
    if result['success']:
        # Create JWT token
        access_token = create_access_token(identity=result['user']['id'])
        result['token'] = access_token
        
        return jsonify(result), 200
    else:
        return jsonify(result), 401

@auth_bp.route('/register', methods=['POST'])
@validate_json(['username', 'password'])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    
    result = create_user(username, password, role)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Get the current user."""
    user_id = get_jwt_identity()
    result = get_user(user_id)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404
