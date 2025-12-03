from datetime import datetime
from api.extensions import db
from api.models.asset_inventory import AssetInventory
from api.models.target import Target
from api.models.scan import Scan
from api.services.banner_grabber import BannerGrabber
import json

class AssetInventoryService:
    """Service for managing asset inventory enrichment"""
    
    def __init__(self):
        self.banner_grabber = BannerGrabber(timeout=5)
    
    def process_scan_results(self, scan_id):
        """
        Process scan results and populate asset inventory
        
        :param scan_id: Scan ID to process
        :return: Number of assets created/updated
        """
        scan = Scan.query.get(scan_id)
        if not scan or not scan.raw_output:
            return 0
        
        try:
            # Parse raw output
            raw_data = json.loads(scan.raw_output)
            results = raw_data.get('results', {})
            
            # Extract OS information
            os_detection = results.get('os_detection')
            if os_detection:
                self._update_target_os(scan.target_id, os_detection)
            
            # Extract service information
            if 'hosts' in results:
                for host in results['hosts']:
                    for port_info in host.get('ports', []):
                        self._create_or_update_asset(
                            scan.target_id,
                            scan_id,
                            port_info,
                            os_detection
                        )
            
            # Trigger banner grabbing for open ports
            self.enrich_with_banners(scan.target_id)
            
            db.session.commit()
            return AssetInventory.query.filter_by(scan_id=scan_id).count()
            
        except Exception as e:
            print(f"Error processing scan results for asset inventory: {e}")
            db.session.rollback()
            return 0
    
    def _update_target_os(self, target_id, os_detection):
        """Update target with latest OS information"""
        target = Target.query.get(target_id)
        if target and os_detection:
            target.os_name = os_detection.get('name')
            target.os_cpe = os_detection.get('cpe')
            target.os_last_detected = datetime.utcnow()
    
    def _create_or_update_asset(self, target_id, scan_id, port_info, os_detection=None):
        """Create or update asset inventory record"""
        
        # Check if asset already exists for this target/port
        existing = AssetInventory.query.filter_by(
            target_id=target_id,
            port=port_info['port'],
            protocol=port_info.get('protocol', 'tcp')
        ).first()
        
        if existing:
            # Update existing asset
            asset = existing
            asset.last_seen = datetime.utcnow()
            asset.scan_id = scan_id
        else:
            # Create new asset
            asset = AssetInventory(
                target_id=target_id,
                scan_id=scan_id,
                port=port_info['port'],
                protocol=port_info.get('protocol', 'tcp'),
                discovered_at=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            db.session.add(asset)
        
        # Update service information
        asset.service_name = port_info.get('service')
        asset.service_product = port_info.get('product')
        asset.service_version = port_info.get('version')
        asset.service_extrainfo = port_info.get('extrainfo')
        
        # Extract service CPE if available
        if 'cpe' in port_info and port_info['cpe']:
            asset.service_cpe = port_info['cpe']
        
        # Update OS information if available
        if os_detection:
            asset.os_name = os_detection.get('name')
            asset.os_vendor = os_detection.get('vendor')
            asset.os_family = os_detection.get('family')
            asset.os_accuracy = os_detection.get('accuracy')
            asset.os_cpe = os_detection.get('cpe')
        
        return asset
    
    def enrich_with_banners(self, target_id):
        """
        Grab banners for all open ports on target
        
        :param target_id: Target ID
        :return: Number of banners grabbed
        """
        target = Target.query.get(target_id)
        if not target:
            return 0
        
        # Get all assets for this target
        assets = AssetInventory.query.filter_by(target_id=target_id).all()
        
        # Collect ports to scan
        ports = [(asset.port, asset.protocol) for asset in assets]
        
        if not ports:
            return 0
        
        # Grab banners
        banners = self.banner_grabber.grab_banners_bulk(target.ip_address, ports)
        
        # Update assets with banner information
        banner_count = 0
        for asset in assets:
            if asset.port in banners:
                banner = banners[asset.port]
                asset.banner = banner
                asset.banner_grabbed_at = datetime.utcnow()
                
                # Try to enrich service info from banner
                enriched = self.banner_grabber.enrich_service_info(
                    banner,
                    asset.port,
                    asset.service_name
                )
                
                # Update service details if banner provides better info
                if enriched['product'] and not asset.service_product:
                    asset.service_product = enriched['product']
                if enriched['version'] and not asset.service_version:
                    asset.service_version = enriched['version']
                
                banner_count += 1
        
        db.session.commit()
        return banner_count
    
    def get_target_assets(self, target_id):
        """
        Get all assets for a target, organized by type
        
        :param target_id: Target ID
        :return: Dictionary with OS info and services
        """
        target = Target.query.get(target_id)
        if not target:
            return None
        
        assets = AssetInventory.query.filter_by(target_id=target_id).order_by(
            AssetInventory.port
        ).all()
        
        # Get unique OS information
        os_info = None
        if target.os_name:
            os_info = {
                'name': target.os_name,
                'cpe': target.os_cpe,
                'last_detected': target.os_last_detected.isoformat() if target.os_last_detected else None
            }
        
        # Organize services by port
        services = []
        for asset in assets:
            services.append({
                'id': asset.id,
                'port': asset.port,
                'protocol': asset.protocol,
                'service': asset.service_name,
                'product': asset.service_product,
                'version': asset.service_version,
                'extrainfo': asset.service_extrainfo,
                'cpe': asset.service_cpe,
                'banner': asset.banner,
                'banner_grabbed_at': asset.banner_grabbed_at.isoformat() if asset.banner_grabbed_at else None,
                'discovered_at': asset.discovered_at.isoformat() if asset.discovered_at else None,
                'last_seen': asset.last_seen.isoformat() if asset.last_seen else None
            })
        
        return {
            'target': {
                'id': target.id,
                'name': target.name,
                'ip_address': target.ip_address
            },
            'os': os_info,
            'services': services,
            'total_services': len(services)
        }
    
    def get_all_cpe_identifiers(self, target_id):
        """Get all unique CPE identifiers for a target"""
        assets = AssetInventory.query.filter_by(target_id=target_id).all()
        
        cpe_list = []
        for asset in assets:
            if asset.os_cpe:
                cpe_list.append({'type': 'os', 'cpe': asset.os_cpe})
            if asset.service_cpe:
                cpe_list.append({'type': 'service', 'cpe': asset.service_cpe, 'port': asset.port})
        
        return cpe_list
