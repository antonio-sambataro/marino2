
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.auth_service import authenticate_user, create_user, get_user, update_user
from app.utils.helpers import validate_json
from app.models.user import User
from app import db

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


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@validate_json(['current_password', 'new_password'])
def change_password():
    """Change user password."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
    
    # Update password
    try:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Password updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error updating password: {str(e)}'
        }), 500