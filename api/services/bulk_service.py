"""
Bulk Service.
Handles bulk operations for targets and vulnerabilities.
"""
from api.models.target import Target
from api.models.scan import Scan
from api.models.vulnerability import VulnerabilityInstance
from api.models.ticket import Ticket
from api.extensions import db
from datetime import datetime

class BulkService:
    """
    Service for performing bulk operations.
    """

    @staticmethod
    def bulk_scan_targets(target_ids, scan_type='quick'):
        """
        Initiate scans for multiple targets.
        
        Args:
            target_ids: List of target IDs.
            scan_type: Type of scan ('quick', 'full', etc.)
            
        Returns:
            List of created scan IDs.
        """
        created_scans = []
        for target_id in target_ids:
            target = Target.query.get(target_id)
            if not target:
                continue
                
            scan = Scan(
                target_id=target_id,
                scan_type=scan_type,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(scan)
            db.session.flush()  # Get ID without committing
            created_scans.append(scan.id)
            
            # In a real implementation, this would trigger the scan task
            # For now, we just create the record
            
        db.session.commit()
        return created_scans

    @staticmethod
    def bulk_assign_group(target_ids, group_id):
        """
        Assign multiple targets to a group.
        
        Args:
            target_ids: List of target IDs.
            group_id: Target Group ID.
            
        Returns:
            Number of updated targets.
        """
        count = Target.query.filter(Target.id.in_(target_ids)).update(
            {Target.group_id: group_id},
            synchronize_session=False
        )
        db.session.commit()
        return count

    @staticmethod
    def bulk_delete_targets(target_ids):
        """
        Delete multiple targets.
        
        Args:
            target_ids: List of target IDs.
            
        Returns:
            Number of deleted targets.
        """
        # Note: Cascade delete should handle related scans/vulns if configured
        # Otherwise we might need to delete related objects first
        count = Target.query.filter(Target.id.in_(target_ids)).delete(synchronize_session=False)
        db.session.commit()
        return count

    @staticmethod
    def bulk_edit_targets(target_ids, data):
        """
        Update properties for multiple targets.
        
        Args:
            target_ids: List of target IDs.
            data: Dictionary of fields to update (description, etc.)
            
        Returns:
            Number of updated targets.
        """
        valid_fields = ['description'] # Add other fields as needed
        update_data = {k: v for k, v in data.items() if k in valid_fields}
        
        if not update_data:
            return 0
            
        count = Target.query.filter(Target.id.in_(target_ids)).update(
            update_data,
            synchronize_session=False
        )
        db.session.commit()
        return count

    @staticmethod
    def bulk_update_vuln_status(vuln_ids, status, false_positive_reason=None):
        """
        Update status for multiple vulnerability instances.
        
        Args:
            vuln_ids: List of vulnerability instance IDs.
            status: New status.
            false_positive_reason: Reason if status is false_positive.
            
        Returns:
            Number of updated instances.
        """
        update_data = {'status': status}
        if status == 'fixed':
            update_data['fixed_at'] = datetime.utcnow()
        if status == 'false_positive' and false_positive_reason:
            update_data['false_positive_reason'] = false_positive_reason
            
        count = VulnerabilityInstance.query.filter(VulnerabilityInstance.id.in_(vuln_ids)).update(
            update_data,
            synchronize_session=False
        )
        db.session.commit()
        return count

    @staticmethod
    def bulk_create_tickets(vuln_ids, ticket_data):
        """
        Create tickets for multiple vulnerabilities.
        
        Args:
            vuln_ids: List of vulnerability instance IDs.
            ticket_data: Dictionary with ticket details (title, priority, etc.)
            
        Returns:
            List of created ticket IDs.
        """
        created_tickets = []
        vulns = VulnerabilityInstance.query.filter(VulnerabilityInstance.id.in_(vuln_ids)).all()
        
        if not vulns:
            return []
            
        # Option 1: Create one ticket for ALL selected vulnerabilities (Bulk Ticket)
        # Check if 'group_ticket' is true in ticket_data
        if ticket_data.get('group_ticket', False):
            ticket = Ticket(
                title=ticket_data.get('title', 'Bulk Remediation Ticket'),
                description=ticket_data.get('description', 'Remediate the following vulnerabilities:\n' + '\n'.join([f"- {v.vulnerability.name} on {v.target.name}" for v in vulns])),
                priority=ticket_data.get('priority', 'Medium'),
                status='open'
            )
            ticket.vulnerabilities.extend(vulns)
            db.session.add(ticket)
            db.session.flush()
            created_tickets.append(ticket.id)
            
        else:
            # Option 2: Create individual tickets for each vulnerability
            for vuln in vulns:
                ticket = Ticket(
                    title=f"{ticket_data.get('title_prefix', 'Remediate')}: {vuln.vulnerability.name}",
                    description=ticket_data.get('description', f"Remediate {vuln.vulnerability.name} on {vuln.target.name}"),
                    priority=ticket_data.get('priority', 'Medium'),
                    status='open'
                )
                ticket.vulnerabilities.append(vuln)
                db.session.add(ticket)
                db.session.flush()
                created_tickets.append(ticket.id)
            
        db.session.commit()
        return created_tickets
