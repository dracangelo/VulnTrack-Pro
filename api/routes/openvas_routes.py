from flask import Blueprint, jsonify
from api.services.openvas_scanner import OpenVASScanner
import os

openvas_bp = Blueprint('openvas', __name__, url_prefix='/api/openvas')

@openvas_bp.route('/configs', methods=['GET'])
def get_configs():
    """Fetch available OpenVAS scan configurations"""
    try:
        scanner = OpenVASScanner(
            host=os.getenv('OPENVAS_HOST', '127.0.0.1'),
            port=int(os.getenv('OPENVAS_PORT', 9390)),
            username=os.getenv('OPENVAS_USERNAME', 'admin'),
            password=os.getenv('OPENVAS_PASSWORD', 'admin')
        )
        
        configs = scanner.get_scan_configs()
        
        return jsonify({
            'success': True,
            'configs': configs
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@openvas_bp.route('/test-connection', methods=['GET'])
def test_connection():
    """Test OpenVAS connection"""
    try:
        scanner = OpenVASScanner(
            host=os.getenv('OPENVAS_HOST', '127.0.0.1'),
            port=int(os.getenv('OPENVAS_PORT', 9390)),
            username=os.getenv('OPENVAS_USERNAME', 'admin'),
            password=os.getenv('OPENVAS_PASSWORD', 'admin')
        )
        
        connected = scanner.connect()
        
        if connected:
            scanner.disconnect()
            return jsonify({
                'success': True,
                'message': 'Successfully connected to OpenVAS'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to OpenVAS'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
