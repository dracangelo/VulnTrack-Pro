from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.asset_inventory import AssetInventory
from api.models.target import Target
from api.services.asset_inventory_service import AssetInventoryService

asset_bp = Blueprint('assets', __name__, url_prefix='/api/assets')

@asset_bp.route('/targets/<int:target_id>/assets', methods=['GET'])
def get_target_assets(target_id):
    """Get all discovered assets for a target"""
    service = AssetInventoryService()
    assets = service.get_target_assets(target_id)
    
    if not assets:
        return jsonify({'error': 'Target not found'}), 404
    
    return jsonify(assets)

@asset_bp.route('/targets/<int:target_id>/os-info', methods=['GET'])
def get_os_information(target_id):
    """Get OS detection results for a target"""
    target = Target.query.get_or_404(target_id)
    
    os_info = {
        'target_id': target.id,
        'target_name': target.name,
        'os_name': target.os_name,
        'os_cpe': target.os_cpe,
        'os_last_detected': target.os_last_detected.isoformat() if target.os_last_detected else None
    }
    
    return jsonify(os_info)

@asset_bp.route('/targets/<int:target_id>/cpe', methods=['GET'])
def get_cpe_identifiers(target_id):
    """Get all CPE identifiers for a target"""
    service = AssetInventoryService()
    cpe_list = service.get_all_cpe_identifiers(target_id)
    
    return jsonify({
        'target_id': target_id,
        'cpe_identifiers': cpe_list,
        'total': len(cpe_list)
    })

@asset_bp.route('/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get specific asset details"""
    asset = AssetInventory.query.get_or_404(asset_id)
    return jsonify(asset.to_dict())

@asset_bp.route('/targets/<int:target_id>/refresh-banners', methods=['POST'])
def refresh_banners(target_id):
    """Manually trigger banner grabbing for target"""
    target = Target.query.get_or_404(target_id)
    
    service = AssetInventoryService()
    banner_count = service.enrich_with_banners(target_id)
    
    return jsonify({
        'message': f'Banner refresh completed',
        'target_id': target_id,
        'banners_grabbed': banner_count
    })

@asset_bp.route('/targets/<int:target_id>/services', methods=['GET'])
def get_target_services(target_id):
    """Get all services discovered on a target"""
    assets = AssetInventory.query.filter_by(target_id=target_id).order_by(
        AssetInventory.port
    ).all()
    
    services = []
    for asset in assets:
        services.append({
            'port': asset.port,
            'protocol': asset.protocol,
            'service': asset.service_name,
            'product': asset.service_product,
            'version': asset.service_version,
            'banner': asset.banner[:100] + '...' if asset.banner and len(asset.banner) > 100 else asset.banner
        })
    
    return jsonify({
        'target_id': target_id,
        'services': services,
        'total': len(services)
    })
