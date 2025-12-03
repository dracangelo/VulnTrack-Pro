from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.ticket import Ticket
from api.models.vulnerability import VulnerabilityInstance

ticket_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@ticket_bp.route('/', methods=['GET'])
def get_tickets():
    tickets = Ticket.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'status': t.status,
        'priority': t.priority,
        'assignee_id': t.assignee_id,
        'vuln_count': len(t.vulnerabilities)
    } for t in tickets])

@ticket_bp.route('/', methods=['POST'])
def create_ticket():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    new_ticket = Ticket(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        assignee_id=data.get('assignee_id')
    )
    db.session.add(new_ticket)
    db.session.commit()
    
    from api.services.activity_service import ActivityService
    # Assuming user_id is passed in data or we have a current_user context (not implemented yet)
    # For now, use None or data.get('user_id')
    ActivityService.log_activity(
        user_id=data.get('user_id'),
        action='create_ticket',
        target_type='Ticket',
        target_id=new_ticket.id,
        details=f"Created ticket: {new_ticket.title}"
    )
    
    return jsonify({'message': 'Ticket created', 'id': new_ticket.id}), 201

@ticket_bp.route('/<int:id>', methods=['GET'])
def get_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    return jsonify({
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'assignee_id': ticket.assignee_id,
        'created_at': ticket.created_at.isoformat(),
        'updated_at': ticket.updated_at.isoformat(),
        'vulnerabilities': [v.to_dict() for v in ticket.vulnerabilities]
    })

@ticket_bp.route('/<int:id>', methods=['DELETE'])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Ticket deleted'})

@ticket_bp.route('/<int:id>', methods=['PUT'])
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.get_json()
    
    old_assignee = ticket.assignee_id
    old_status = ticket.status
    
    ticket.title = data.get('title', ticket.title)
    ticket.description = data.get('description', ticket.description)
    ticket.status = data.get('status', ticket.status)
    ticket.priority = data.get('priority', ticket.priority)
    ticket.assignee_id = data.get('assignee_id', ticket.assignee_id)
    
    db.session.commit()
    
    from api.services.activity_service import ActivityService
    
    # Log status change
    if old_status != ticket.status:
        ActivityService.log_activity(
            user_id=data.get('user_id'),
            action='update_ticket_status',
            target_type='Ticket',
            target_id=ticket.id,
            details=f"Status changed from {old_status} to {ticket.status}"
        )
    
    # Notify if assigned
    if ticket.assignee_id and ticket.assignee_id != old_assignee:
        from api.services.notification_service import NotificationService
        NotificationService.notify_ticket_assignment(ticket, ticket.assignee_id)
        
    return jsonify({'message': 'Ticket updated'})

@ticket_bp.route('/<int:id>/bind', methods=['POST'])
def bind_vulns(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.get_json()
    
    if 'vuln_ids' not in data:
        return jsonify({'error': 'vuln_ids required'}), 400
        
    for vuln_id in data['vuln_ids']:
        vuln_instance = VulnerabilityInstance.query.get(vuln_id)
        if vuln_instance and vuln_instance not in ticket.vulnerabilities:
            ticket.vulnerabilities.append(vuln_instance)
            
    db.session.commit()
    return jsonify({'message': 'Vulnerabilities bound to ticket'})

@ticket_bp.route('/create-from-vuln', methods=['POST'])
def create_ticket_from_vuln():
    """
    Create a ticket and automatically bind a vulnerability instance.
    One-click ticket creation from vulnerability details.
    
    Expects:
    - title: Ticket title
    - description: Ticket description
    - priority: Ticket priority (high, medium, low)
    - status: Ticket status (default: open)
    - vuln_instance_id: ID of the vulnerability instance to bind
    - assignee_id: Optional assignee ID
    """
    data = request.get_json()
    
    # Validate required fields
    if not data or 'title' not in data or 'vuln_instance_id' not in data:
        return jsonify({'error': 'title and vuln_instance_id are required'}), 400
    
    # Verify vulnerability instance exists
    vuln_instance = VulnerabilityInstance.query.get(data['vuln_instance_id'])
    if not vuln_instance:
        return jsonify({'error': 'Vulnerability instance not found'}), 404
    
    # Create ticket
    new_ticket = Ticket(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'open'),
        assignee_id=data.get('assignee_id')
    )
    db.session.add(new_ticket)
    db.session.flush()  # Get the ticket ID before commit
    
    # Bind vulnerability to ticket
    new_ticket.vulnerabilities.append(vuln_instance)
    
    db.session.commit()
    
    # Log activity
    from api.services.activity_service import ActivityService
    ActivityService.log_activity(
        user_id=data.get('user_id'),
        action='create_ticket_from_vuln',
        target_type='Ticket',
        target_id=new_ticket.id,
        details=f"Created ticket from vulnerability: {new_ticket.title}"
    )
    
    return jsonify({
        'message': 'Ticket created and vulnerability bound successfully',
        'ticket_id': new_ticket.id,
        'ticket': {
            'id': new_ticket.id,
            'title': new_ticket.title,
            'status': new_ticket.status,
            'priority': new_ticket.priority,
            'vuln_count': len(new_ticket.vulnerabilities)
        }
    }), 201
