from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.sync_service import import_data, export_data, sync_with_pos
from app.utils.helpers import admin_required

sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

@sync_bp.route('/import', methods=['POST'])
@jwt_required()
@admin_required
def import_json():
    """Import data from JSON file."""
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Missing JSON data'}), 400
    
    data = request.get_json()
    result = import_data(data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@sync_bp.route('/export', methods=['GET'])
@jwt_required()
@admin_required
def export_json():
    """Export all data to JSON."""
    result = export_data()
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@sync_bp.route('/sync-pos', methods=['GET'])
@jwt_required()
@admin_required
def sync_pos():
    """Sync with external POS system."""
    try:
        result = sync_with_pos()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error synchronizing with POS: {str(e)}'
        }), 500

@sync_bp.route('/check-sync', methods=['GET'])
def check_sync_status():
    """Check the synchronization status."""
    # This endpoint can be used to check if the data is in sync with the POS system
    # For now, just return a placeholder response
    return jsonify({
        'success': True,
        'status': 'ok',
        'last_sync': '2023-05-03T12:00:00Z',
        'message': 'Data is in sync'
    }), 200
