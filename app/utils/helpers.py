from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User

def validate_json(required_fields=None):
    """Decorator to validate JSON request data."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if request contains JSON
            if not request.is_json:
                return jsonify({'success': False, 'message': 'Missing JSON data'}), 400
            
            # Check if required fields are present
            if required_fields:
                data = request.get_json()
                for field in required_fields:
                    if field not in data:
                        return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to require admin role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Verify JWT
        verify_jwt_in_request()
        
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
