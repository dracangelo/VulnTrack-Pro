from flask import Blueprint, jsonify
from api.services.openvas_scanner import OpenVASScanner
import os
import logging

logger = logging.getLogger(__name__)

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
        
        logger.info("Fetching OpenVAS scan configurations...")
        configs = scanner.get_scan_configs()
        logger.info(f"Found {len(configs)} configurations")
        
        return jsonify(configs), 200
        
    except Exception as e:
        logger.error(f"Error fetching OpenVAS configs: {e}")
        return jsonify({
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
        
        success, message = scanner.test_connection()
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing OpenVAS connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
