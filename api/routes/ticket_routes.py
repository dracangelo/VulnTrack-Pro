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

@ticket_bp.route('/<int:id>', methods=['PUT'])
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    data = request.get_json()
    
    old_assignee = ticket.assignee_id
    ticket.title = data.get('title', ticket.title)
    ticket.description = data.get('description', ticket.description)
    ticket.status = data.get('status', ticket.status)
    ticket.priority = data.get('priority', ticket.priority)
    ticket.assignee_id = data.get('assignee_id', ticket.assignee_id)
    
    db.session.commit()
    
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
