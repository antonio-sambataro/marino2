from app import db
from app.models.user import User

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if not user.check_password(password):
            return {'success': False, 'message': 'Invalid password'}
        
        return {
            'success': True,
            'user': user.to_dict(),
            'message': 'Authentication successful'
        }
    except Exception as e:
        return {'success': False, 'message': f'Authentication error: {str(e)}'}

def create_user(username, password, role='user'):
    """Create a new user."""
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return {'success': False, 'message': 'Username already exists'}
        
        # Create new user
        user = User(username=username, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return {
            'success': True,
            'user': user.to_dict(),
            'message': 'User created successfully'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error creating user: {str(e)}'}

def get_user(user_id):
    """Get a user by ID."""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        return {
            'success': True,
            'user': user.to_dict()
        }
    except Exception as e:
        return {'success': False, 'message': f'Error retrieving user: {str(e)}'}

def update_user(user_id, data):
    """Update a user."""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        # Update user fields
        if 'username' in data:
            # Check if new username already exists
            if data['username'] != user.username:
                existing_user = User.query.filter_by(username=data['username']).first()
                if existing_user:
                    return {'success': False, 'message': 'Username already exists'}
                user.username = data['username']
        
        if 'password' in data:
            user.set_password(data['password'])
        
        if 'role' in data:
            user.role = data['role']
        
        db.session.commit()
        
        return {
            'success': True,
            'user': user.to_dict(),
            'message': 'User updated successfully'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error updating user: {str(e)}'}

def delete_user(user_id):
    """Delete a user."""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        db.session.delete(user)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'User deleted successfully'
        }
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error deleting user: {str(e)}'}
