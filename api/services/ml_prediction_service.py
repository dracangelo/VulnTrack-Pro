from datetime import datetime, timedelta
from api.services.ml_data_service import MLDataService
import pandas as pd

class MLPredictionService:
    """Simple ML-based vulnerability trend prediction using Prophet"""
    
    def __init__(self):
        self.data_service = MLDataService()
        self.models = {}  # Cache trained models
        self.cache_ttl = timedelta(hours=24)
        self.last_trained = {}
    
    def predict_vulnerability_trend(self, days_ahead=30):
        """
        Predict vulnerability discovery rate
        
        :param days_ahead: Number of days to predict ahead
        :return: Dictionary with predictions, trend, and confidence
        """
        try:
            from prophet import Prophet
        except ImportError:
            return {'error': 'Prophet library not installed. Run: pip install prophet'}
        
        # Get historical data
        data = self.data_service.get_vulnerability_time_series(days=90)
        
        if data.empty or len(data) < 10:
            return {
                'error': 'Insufficient historical data',
                'message': 'Need at least 10 days of vulnerability data for predictions'
            }
        
        # Train Prophet model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05
        )
        
        model.fit(data)
        
        # Make predictions
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Format results
        return self._format_predictions(forecast, days_ahead, data)
    
    def predict_severity_distribution(self, days_ahead=30):
        """
        Predict future severity distribution
        
        :param days_ahead: Number of days to predict ahead
        :return: Dictionary with predictions for each severity
        """
        try:
            from prophet import Prophet
        except ImportError:
            return {'error': 'Prophet library not installed'}
        
        predictions = {}
        severities = ['Critical', 'High', 'Medium', 'Low']
        
        for severity in severities:
            data = self.data_service.get_severity_time_series(severity, days=90)
            
            if data.empty or len(data) < 10:
                predictions[severity] = {
                    'error': 'Insufficient data',
                    'predictions': []
                }
                continue
            
            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=False
            )
            
            model.fit(data)
            
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)
            
            predictions[severity] = self._format_predictions(forecast, days_ahead, data)
        
        return predictions
    
    def predict_target_risk(self, target_id, days_ahead=30):
        """
        Predict vulnerability trend for specific target
        
        :param target_id: Target ID
        :param days_ahead: Number of days to predict ahead
        :return: Dictionary with predictions
        """
        try:
            from prophet import Prophet
        except ImportError:
            return {'error': 'Prophet library not installed'}
        
        data = self.data_service.get_target_vulnerability_history(target_id, days=90)
        
        if data.empty or len(data) < 10:
            return {
                'error': 'Insufficient historical data',
                'message': f'Need at least 10 days of data for target {target_id}'
            }
        
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        
        model.fit(data)
        
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        return self._format_predictions(forecast, days_ahead, data)
    
    def get_ml_insights(self):
        """
        Get overall ML insights and predictions
        
        :return: Dictionary with insights and recommendations
        """
        # Get vulnerability trend
        vuln_trend = self.predict_vulnerability_trend(30)
        
        if 'error' in vuln_trend:
            return {
                'error': vuln_trend['error'],
                'message': 'Unable to generate insights due to insufficient data'
            }
        
        # Get severity distribution
        severity_dist = self.predict_severity_distribution(30)
        
        # Calculate predicted totals
        predicted_next_month = sum(p['predicted'] for p in vuln_trend['predictions'])
        
        # Generate insights
        insights = {
            'overall_trend': vuln_trend['trend'],
            'predicted_next_month': int(predicted_next_month),
            'confidence': vuln_trend['confidence'],
            'severity_trends': {},
            'recommendations': []
        }
        
        # Add severity trends
        for severity, data in severity_dist.items():
            if 'error' not in data:
                insights['severity_trends'][severity] = data['trend']
        
        # Generate recommendations
        insights['recommendations'] = self._generate_recommendations(vuln_trend, severity_dist)
        
        return insights
    
    def _format_predictions(self, forecast, days_ahead, historical_data):
        """
        Format Prophet forecast into API response
        
        :param forecast: Prophet forecast DataFrame
        :param days_ahead: Number of days predicted
        :param historical_data: Original historical data
        :return: Formatted dictionary
        """
        # Get only future predictions
        future_forecast = forecast.tail(days_ahead)
        
        predictions = []
        for _, row in future_forecast.iterrows():
            predictions.append({
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted': max(0, int(row['yhat'])),  # Ensure non-negative
                'lower': max(0, int(row['yhat_lower'])),
                'upper': max(0, int(row['yhat_upper']))
            })
        
        # Calculate trend
        trend = self._calculate_trend(forecast, historical_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(forecast, days_ahead)
        
        return {
            'predictions': predictions,
            'trend': trend,
            'confidence': confidence
        }
    
    def _calculate_trend(self, forecast, historical_data):
        """
        Calculate if trend is increasing, decreasing, or stable
        
        :param forecast: Prophet forecast DataFrame
        :param historical_data: Original historical data
        :return: String ('increasing', 'decreasing', 'stable')
        """
        if historical_data.empty:
            return 'unknown'
        
        # Compare recent historical average to predicted average
        historical_avg = historical_data.tail(14)['y'].mean()
        predicted_avg = forecast.tail(14)['yhat'].mean()
        
        if predicted_avg > historical_avg * 1.15:
            return 'increasing'
        elif predicted_avg < historical_avg * 0.85:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_confidence(self, forecast, days_ahead):
        """
        Calculate prediction confidence based on interval width
        
        :param forecast: Prophet forecast DataFrame
        :param days_ahead: Number of days predicted
        :return: Float between 0 and 1
        """
        future_forecast = forecast.tail(days_ahead)
        
        # Calculate average interval width
        avg_width = (future_forecast['yhat_upper'] - future_forecast['yhat_lower']).mean()
        avg_value = future_forecast['yhat'].mean()
        
        if avg_value == 0:
            return 0.5
        
        # Narrower intervals = higher confidence
        # Confidence decreases as interval width increases relative to predicted value
        relative_width = avg_width / max(avg_value, 1)
        confidence = max(0, min(1, 1 - (relative_width / 2)))
        
        return round(confidence, 2)
    
    def _generate_recommendations(self, vuln_trend, severity_dist):
        """
        Generate actionable recommendations based on predictions
        
        :param vuln_trend: Vulnerability trend predictions
        :param severity_dist: Severity distribution predictions
        :return: List of recommendation dictionaries
        """
        recommendations = []
        
        # Check overall trend
        if vuln_trend['trend'] == 'increasing':
            recommendations.append({
                'type': 'warning',
                'priority': 'high',
                'message': 'Vulnerability discovery rate is increasing. Consider increasing scan frequency and remediation resources.'
            })
        elif vuln_trend['trend'] == 'decreasing':
            recommendations.append({
                'type': 'success',
                'priority': 'low',
                'message': 'Vulnerability discovery rate is decreasing. Current security measures appear effective.'
            })
        
        # Check critical vulnerabilities
        if 'Critical' in severity_dist and 'error' not in severity_dist['Critical']:
            if severity_dist['Critical']['trend'] == 'increasing':
                recommendations.append({
                    'type': 'critical',
                    'priority': 'critical',
                    'message': 'Critical vulnerabilities are trending upward. Immediate action required to prioritize remediation.'
                })
        
        # Check high vulnerabilities
        if 'High' in severity_dist and 'error' not in severity_dist['High']:
            if severity_dist['High']['trend'] == 'increasing':
                recommendations.append({
                    'type': 'warning',
                    'priority': 'high',
                    'message': 'High severity vulnerabilities are increasing. Allocate additional remediation resources.'
                })
        
        # Low confidence warning
        if vuln_trend['confidence'] < 0.5:
            recommendations.append({
                'type': 'info',
                'priority': 'medium',
                'message': 'Prediction confidence is low. Consider collecting more historical data for better accuracy.'
            })
        
        return recommendations
