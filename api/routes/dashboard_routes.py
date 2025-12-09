"""
Dashboard analytics routes.
Provides data for dashboard visualizations including timeline, maps, and heat maps.
"""
from flask import Blueprint, jsonify, request
from api.models.vulnerability import VulnerabilityInstance, Vulnerability
from api.models.scan import Scan
from api.models.target import Target
from api.models.target import TargetGroup
from api.extensions import db
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
from collections import defaultdict
import ipaddress

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/vulnerability-timeline', methods=['GET'])
def get_vulnerability_timeline():
    """
    Get vulnerability timeline data for line chart.
    
    Query params:
        days: Number of days to look back (default: 30)
        severity: Filter by severity (optional)
        target_id: Filter by target (optional)
    """
    days = request.args.get('days', 30, type=int)
    severity = request.args.get('severity')
    target_id = request.args.get('target_id', type=int)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Build query
    query = VulnerabilityInstance.query.filter(
        VulnerabilityInstance.detected_at >= start_date
    )
    
    if severity:
        query = query.join(Vulnerability).filter(Vulnerability.severity == severity)
    
    if target_id:
        query = query.join(Scan).filter(Scan.target_id == target_id)
    
    vulnerabilities = query.all()
    
    # Group by day
    timeline_data = defaultdict(lambda: {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0, 'total': 0})
    
    for vuln_instance in vulnerabilities:
        if not vuln_instance.detected_at:
            continue
        
        day_key = vuln_instance.detected_at.strftime('%Y-%m-%d')
        severity_level = vuln_instance.vulnerability.severity.lower()
        
        timeline_data[day_key][severity_level] += 1
        timeline_data[day_key]['total'] += 1
    
    # Convert to sorted list
    timeline = []
    current_date = start_date
    while current_date <= end_date:
        day_key = current_date.strftime('%Y-%m-%d')
        timeline.append({
            'date': day_key,
            **timeline_data[day_key]
        })
        current_date += timedelta(days=1)
    
    return jsonify({
        'timeline': timeline,
        'period_days': days,
        'total_vulnerabilities': len(vulnerabilities)
    }), 200


@dashboard_bp.route('/attack-surface', methods=['GET'])
def get_attack_surface():
    """
    Get attack surface map data for network diagram.
    
    Returns:
        - Nodes: targets with vulnerability counts
        - Edges: relationships between targets and groups
        - Metrics: overall attack surface metrics
    """
    # Get all targets with vulnerability counts
    targets = Target.query.all()
    
    nodes = []
    for target in targets:
        # Count vulnerabilities per target
        vuln_count = db.session.query(func.count(VulnerabilityInstance.id)).join(
            Scan
        ).filter(Scan.target_id == target.id).scalar() or 0
        
        # Get severity breakdown
        severity_counts = db.session.query(
            Vulnerability.severity,
            func.count(VulnerabilityInstance.id)
        ).join(VulnerabilityInstance).join(Scan).filter(
            Scan.target_id == target.id
        ).group_by(Vulnerability.severity).all()
        
        severity_dict = {sev.lower(): count for sev, count in severity_counts}
        
        # Determine risk level
        critical_high = severity_dict.get('critical', 0) + severity_dict.get('high', 0)
        if critical_high > 10:
            risk_level = 'critical'
        elif critical_high > 5:
            risk_level = 'high'
        elif vuln_count > 10:
            risk_level = 'medium'
        elif vuln_count > 0:
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        nodes.append({
            'id': target.id,
            'name': target.name or target.ip_address,
            'ip_address': target.ip_address,
            'vulnerability_count': vuln_count,
            'severity_counts': severity_dict,
            'risk_level': risk_level,
            'group_id': target.group_id
        })
    
    # Get groups for edges
    groups = TargetGroup.query.all()
    edges = []
    
    for group in groups:
        group_targets = [n for n in nodes if n['group_id'] == group.id]
        for node in group_targets:
            edges.append({
                'source': group.id + 10000,  # Offset to avoid ID collision
                'target': node['id'],
                'type': 'group_membership'
            })
    
    # Add group nodes
    for group in groups:
        group_vuln_count = sum(n['vulnerability_count'] for n in nodes if n['group_id'] == group.id)
        nodes.append({
            'id': group.id + 10000,
            'name': group.name,
            'type': 'group',
            'vulnerability_count': group_vuln_count,
            'member_count': len([n for n in nodes if n['group_id'] == group.id])
        })
    
    # Calculate metrics
    total_targets = len([n for n in nodes if 'type' not in n])
    total_vulns = sum(n['vulnerability_count'] for n in nodes if 'type' not in n)
    high_risk_targets = len([n for n in nodes if n.get('risk_level') in ['critical', 'high']])
    
    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'metrics': {
            'total_targets': total_targets,
            'total_vulnerabilities': total_vulns,
            'high_risk_targets': high_risk_targets,
            'avg_vulns_per_target': total_vulns / max(total_targets, 1)
        }
    }), 200


@dashboard_bp.route('/risk-heatmap', methods=['GET'])
def get_risk_heatmap():
    """
    Get risk heat map data by subnet/group.
    
    Returns:
        - Heat map cells with risk scores
        - Color-coded by risk level
    """
    # Get all targets
    targets = Target.query.all()
    
    # Group by subnet (first 3 octets for IPv4)
    subnet_data = defaultdict(lambda: {
        'targets': [],
        'total_vulns': 0,
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'info': 0
    })
    
    for target in targets:
        try:
            # Parse IP and get subnet
            ip = ipaddress.ip_address(target.ip_address)
            if ip.version == 4:
                # Get /24 subnet
                octets = target.ip_address.split('.')
                subnet = f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
            else:
                # For IPv6, use first 4 groups
                subnet = str(ipaddress.ip_network(f"{target.ip_address}/64", strict=False))
        except:
            subnet = "Unknown"
        
        # Get vulnerability counts
        vuln_counts = db.session.query(
            Vulnerability.severity,
            func.count(VulnerabilityInstance.id)
        ).join(VulnerabilityInstance).join(Scan).filter(
            Scan.target_id == target.id
        ).group_by(Vulnerability.severity).all()
        
        total_vulns = sum(count for _, count in vuln_counts)
        
        subnet_data[subnet]['targets'].append(target.ip_address)
        subnet_data[subnet]['total_vulns'] += total_vulns
        
        for severity, count in vuln_counts:
            subnet_data[subnet][severity.lower()] += count
    
    # Convert to heat map format
    heatmap = []
    for subnet, data in subnet_data.items():
        # Calculate risk score (0-100)
        risk_score = min(100, (
            data['critical'] * 10 +
            data['high'] * 5 +
            data['medium'] * 2 +
            data['low'] * 1 +
            data['info'] * 0.5
        ))
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 20:
            risk_level = 'medium'
        elif risk_score > 0:
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        heatmap.append({
            'subnet': subnet,
            'target_count': len(data['targets']),
            'total_vulnerabilities': data['total_vulns'],
            'severity_counts': {
                'critical': data['critical'],
                'high': data['high'],
                'medium': data['medium'],
                'low': data['low'],
                'info': data['info']
            },
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level
        })
    
    # Sort by risk score descending
    heatmap.sort(key=lambda x: x['risk_score'], reverse=True)
    
    # Also get group-based heat map
    groups = TargetGroup.query.all()
    group_heatmap = []
    
    for group in groups:
        group_targets = Target.query.filter_by(group_id=group.id).all()
        
        total_vulns = 0
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        
        for target in group_targets:
            vuln_counts = db.session.query(
                Vulnerability.severity,
                func.count(VulnerabilityInstance.id)
            ).join(VulnerabilityInstance).join(Scan).filter(
                Scan.target_id == target.id
            ).group_by(Vulnerability.severity).all()
            
            total_vulns += sum(count for _, count in vuln_counts)
            
            for severity, count in vuln_counts:
                severity_counts[severity.lower()] += count
        
        # Calculate risk score
        risk_score = min(100, (
            severity_counts['critical'] * 10 +
            severity_counts['high'] * 5 +
            severity_counts['medium'] * 2 +
            severity_counts['low'] * 1 +
            severity_counts['info'] * 0.5
        ))
        
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 20:
            risk_level = 'medium'
        elif risk_score > 0:
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        group_heatmap.append({
            'group_id': group.id,
            'group_name': group.name,
            'target_count': len(group_targets),
            'total_vulnerabilities': total_vulns,
            'severity_counts': severity_counts,
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level
        })
    
    group_heatmap.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return jsonify({
        'subnet_heatmap': heatmap,
        'group_heatmap': group_heatmap
    }), 200


@dashboard_bp.route('/metrics', methods=['GET'])
def get_dashboard_metrics():
    """
    Get high-level dashboard metrics.
    
    Returns:
        - scan_coverage: % of targets scanned
        - mttr: Mean Time To Remediate (in days)
        - age_distribution: Vulnerability counts by age buckets
    """
    # 1. Scan Coverage
    total_targets = Target.query.count()
    scanned_targets = db.session.query(func.count(distinct(Scan.target_id))).scalar() or 0
    
    scan_coverage = (scanned_targets / total_targets * 100) if total_targets > 0 else 0
    
    # 2. MTTR (Mean Time To Remediate)
    # Average time between detected_at and fixed_at for fixed vulnerabilities
    mttr_query = db.session.query(
        func.avg(
            func.extract('epoch', VulnerabilityInstance.fixed_at) - 
            func.extract('epoch', VulnerabilityInstance.detected_at)
        )
    ).filter(
        VulnerabilityInstance.status == 'fixed',
        VulnerabilityInstance.fixed_at.isnot(None),
        VulnerabilityInstance.detected_at.isnot(None)
    )
    
    avg_seconds = mttr_query.scalar()
    mttr_days = round(avg_seconds / 86400, 1) if avg_seconds else 0
    
    # 3. Vulnerability Age Distribution (for Open vulnerabilities)
    now = datetime.utcnow()
    age_buckets = {
        '< 30 days': 0,
        '30-60 days': 0,
        '60-90 days': 0,
        '> 90 days': 0
    }
    
    open_vulns = VulnerabilityInstance.query.filter(
        VulnerabilityInstance.status == 'open',
        VulnerabilityInstance.detected_at.isnot(None)
    ).all()
    
    for vuln in open_vulns:
        age_days = (now - vuln.detected_at).days
        
        if age_days < 30:
            age_buckets['< 30 days'] += 1
        elif age_days < 60:
            age_buckets['30-60 days'] += 1
        elif age_days < 90:
            age_buckets['60-90 days'] += 1
        else:
            age_buckets['> 90 days'] += 1
            

from api.models.dashboard import DashboardConfig
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models.user import User

@dashboard_bp.route('/layout', methods=['GET'])
@jwt_required()
def get_dashboard_layout():
    """
    Get the user's preferred dashboard layout.
    Returns the default layout if no custom layout exists.
    """
    current_user_id = get_jwt_identity()
    
    # Try to find user's default config
    config = DashboardConfig.query.filter_by(
        user_id=current_user_id, 
        is_default=True
    ).first()
    
    # If no default, get the most recently updated one
    if not config:
        config = DashboardConfig.query.filter_by(
            user_id=current_user_id
        ).order_by(DashboardConfig.updated_at.desc()).first()
        
    if not config:
        # Return a standard default layout structure
        default_layout = {
            "widgets": [
                {"id": "metrics_cards", "x": 0, "y": 0, "w": 12, "h": 2},
                {"id": "vuln_timeline", "x": 0, "y": 2, "w": 8, "h": 4},
                {"id": "risk_heatmap", "x": 8, "y": 2, "w": 4, "h": 4},
                {"id": "attack_surface", "x": 0, "y": 6, "w": 12, "h": 6}
            ]
        }
        return jsonify({
            'layout_data': default_layout,
            'is_system_default': True
        }), 200
        
    return jsonify(config.to_dict()), 200

@dashboard_bp.route('/layout', methods=['POST'])
@jwt_required()
def save_dashboard_layout():
    """
    Save a dashboard layout configuration.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'layout_data' not in data:
        return jsonify({'error': 'Missing layout_data'}), 400
        
    layout_data = data['layout_data']
    name = data.get('name', 'My Dashboard')
    is_default = data.get('is_default', True)
    
    # If setting as default, unset other defaults for this user
    if is_default:
        DashboardConfig.query.filter_by(
            user_id=current_user_id,
            is_default=True
        ).update({'is_default': False})
    
    # Check if we should update an existing config or create new
    config_id = data.get('id')
    if config_id:
        config = DashboardConfig.query.filter_by(id=config_id, user_id=current_user_id).first()
        if config:
            config.layout_data = layout_data
            config.name = name
            config.is_default = is_default
        else:
            return jsonify({'error': 'Config not found'}), 404
    else:
        # Create new config
        config = DashboardConfig(
            user_id=current_user_id,
            name=name,
            layout_data=layout_data,
            is_default=is_default
        )
        db.session.add(config)
    
    db.session.commit()
    return jsonify(config.to_dict()), 200

