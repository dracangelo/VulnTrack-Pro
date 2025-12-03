from flask import Blueprint, jsonify, request
from api.services.ml_prediction_service import MLPredictionService

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

@ml_bp.route('/predictions/vulnerability-trend', methods=['GET'])
def get_vulnerability_trend():
    """Get vulnerability discovery rate prediction"""
    days_ahead = request.args.get('days', 30, type=int)
    
    # Validate days_ahead
    if days_ahead < 1 or days_ahead > 90:
        return jsonify({'error': 'days must be between 1 and 90'}), 400
    
    service = MLPredictionService()
    predictions = service.predict_vulnerability_trend(days_ahead)
    
    if 'error' in predictions:
        return jsonify(predictions), 400
    
    return jsonify(predictions)

@ml_bp.route('/predictions/severity-distribution', methods=['GET'])
def get_severity_distribution():
    """Get predicted severity distribution"""
    days_ahead = request.args.get('days', 30, type=int)
    
    if days_ahead < 1 or days_ahead > 90:
        return jsonify({'error': 'days must be between 1 and 90'}), 400
    
    service = MLPredictionService()
    predictions = service.predict_severity_distribution(days_ahead)
    
    return jsonify(predictions)

@ml_bp.route('/predictions/target-risk/<int:target_id>', methods=['GET'])
def get_target_risk(target_id):
    """Get risk prediction for specific target"""
    days_ahead = request.args.get('days', 30, type=int)
    
    if days_ahead < 1 or days_ahead > 90:
        return jsonify({'error': 'days must be between 1 and 90'}), 400
    
    service = MLPredictionService()
    predictions = service.predict_target_risk(target_id, days_ahead)
    
    if 'error' in predictions:
        return jsonify(predictions), 400
    
    return jsonify(predictions)

@ml_bp.route('/insights/summary', methods=['GET'])
def get_ml_insights():
    """Get overall ML insights and predictions"""
    service = MLPredictionService()
    insights = service.get_ml_insights()
    
    if 'error' in insights:
        return jsonify(insights), 400
    
    return jsonify(insights)

@ml_bp.route('/health', methods=['GET'])
def ml_health_check():
    """Check if ML service is available"""
    try:
        from prophet import Prophet
        return jsonify({
            'status': 'healthy',
            'prophet_available': True,
            'message': 'ML prediction service is ready'
        })
    except ImportError:
        return jsonify({
            'status': 'degraded',
            'prophet_available': False,
            'message': 'Prophet library not installed. Run: pip install prophet'
        }), 503
