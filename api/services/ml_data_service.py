from datetime import datetime, timedelta
from api.extensions import db
from api.models.vulnerability import VulnerabilityInstance
from api.models.scan import Scan
import pandas as pd
from sqlalchemy import func

class MLDataService:
    """Aggregate vulnerability data for ML training and predictions"""
    
    def get_vulnerability_time_series(self, days=90):
        """
        Get daily vulnerability counts for time-series analysis
        Returns: DataFrame with columns [ds, y] (Prophet format)
        
        :param days: Number of days of historical data
        :return: pandas DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query vulnerability instances grouped by date
        results = db.session.query(
            func.date(VulnerabilityInstance.detected_at).label('date'),
            func.count(VulnerabilityInstance.id).label('count')
        ).filter(
            VulnerabilityInstance.detected_at >= start_date
        ).group_by(
            func.date(VulnerabilityInstance.detected_at)
        ).order_by('date').all()
        
        # Convert to DataFrame in Prophet format
        data = []
        for result in results:
            data.append({
                'ds': result.date,
                'y': result.count
            })
        
        df = pd.DataFrame(data)
        
        # Fill missing dates with 0
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.set_index('ds').resample('D').sum().fillna(0).reset_index()
        
        return df
    
    def get_severity_time_series(self, severity, days=90):
        """
        Get time-series for specific severity level
        
        :param severity: Severity level (Critical, High, Medium, Low, Info)
        :param days: Number of days of historical data
        :return: pandas DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query vulnerability instances for specific severity
        results = db.session.query(
            func.date(VulnerabilityInstance.detected_at).label('date'),
            func.count(VulnerabilityInstance.id).label('count')
        ).join(
            VulnerabilityInstance.vulnerability
        ).filter(
            VulnerabilityInstance.detected_at >= start_date,
            VulnerabilityInstance.vulnerability.has(severity=severity)
        ).group_by(
            func.date(VulnerabilityInstance.detected_at)
        ).order_by('date').all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'ds': result.date,
                'y': result.count
            })
        
        df = pd.DataFrame(data)
        
        # Fill missing dates with 0
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.set_index('ds').resample('D').sum().fillna(0).reset_index()
        
        return df
    
    def get_target_vulnerability_history(self, target_id, days=90):
        """
        Get vulnerability history for specific target
        
        :param target_id: Target ID
        :param days: Number of days of historical data
        :return: pandas DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query vulnerability instances for specific target
        results = db.session.query(
            func.date(VulnerabilityInstance.detected_at).label('date'),
            func.count(VulnerabilityInstance.id).label('count')
        ).filter(
            VulnerabilityInstance.target_id == target_id,
            VulnerabilityInstance.detected_at >= start_date
        ).group_by(
            func.date(VulnerabilityInstance.detected_at)
        ).order_by('date').all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'ds': result.date,
                'y': result.count
            })
        
        df = pd.DataFrame(data)
        
        # Fill missing dates with 0
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.set_index('ds').resample('D').sum().fillna(0).reset_index()
        
        return df
    
    def get_remediation_time_series(self, days=90):
        """
        Get average time to remediation over time
        
        :param days: Number of days of historical data
        :return: pandas DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query fixed vulnerabilities with time to fix
        results = db.session.query(
            func.date(VulnerabilityInstance.fixed_at).label('date'),
            func.avg(
                func.julianday(VulnerabilityInstance.fixed_at) - 
                func.julianday(VulnerabilityInstance.detected_at)
            ).label('avg_days')
        ).filter(
            VulnerabilityInstance.status == 'fixed',
            VulnerabilityInstance.fixed_at >= start_date,
            VulnerabilityInstance.fixed_at.isnot(None)
        ).group_by(
            func.date(VulnerabilityInstance.fixed_at)
        ).order_by('date').all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'ds': result.date,
                'y': result.avg_days if result.avg_days else 0
            })
        
        df = pd.DataFrame(data)
        
        # Fill missing dates
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.set_index('ds').resample('D').mean().fillna(method='ffill').reset_index()
        
        return df
    
    def get_scan_frequency_data(self, days=90):
        """
        Get scan frequency over time
        
        :param days: Number of days of historical data
        :return: pandas DataFrame
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query scans grouped by date
        results = db.session.query(
            func.date(Scan.started_at).label('date'),
            func.count(Scan.id).label('count')
        ).filter(
            Scan.started_at >= start_date
        ).group_by(
            func.date(Scan.started_at)
        ).order_by('date').all()
        
        # Convert to DataFrame
        data = []
        for result in results:
            data.append({
                'ds': result.date,
                'y': result.count
            })
        
        df = pd.DataFrame(data)
        
        # Fill missing dates with 0
        if not df.empty:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.set_index('ds').resample('D').sum().fillna(0).reset_index()
        
        return df
    
    def prepare_training_data(self):
        """
        Prepare all datasets for model training
        
        :return: Dictionary of DataFrames
        """
        return {
            'vulnerability_trend': self.get_vulnerability_time_series(),
            'critical': self.get_severity_time_series('Critical'),
            'high': self.get_severity_time_series('High'),
            'medium': self.get_severity_time_series('Medium'),
            'low': self.get_severity_time_series('Low'),
            'remediation': self.get_remediation_time_series(),
            'scan_frequency': self.get_scan_frequency_data()
        }
