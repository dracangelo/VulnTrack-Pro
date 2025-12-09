from flask import Blueprint, jsonify, request
from api.models.team import Team
from api.models.user import User
from api.models.invitation import TeamInvitation
from api.services.email_service import EmailService
from api.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

team_bp = Blueprint('teams', __name__, url_prefix='/api/teams')

@team_bp.route('/', methods=['GET'])
@jwt_required()
def get_teams():
    """Get all teams."""
    teams = Team.query.all()
    return jsonify([t.to_dict() for t in teams])

@team_bp.route('/', methods=['POST'])
@jwt_required()
def create_team():
    """Create a new team."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing name'}), 400
        
    if Team.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Team name already exists'}), 409
        
    team = Team(
        name=data['name'],
        description=data.get('description')
    )
    
    # Add creator as member
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user:
        team.members.append(user)
        
    db.session.add(team)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Check for integrity error (unique constraint)
        if 'UNIQUE constraint failed' in str(e) or 'IntegrityError' in str(e):
            return jsonify({'error': 'Team name already exists'}), 409
        return jsonify({'error': 'Failed to create team'}), 500
    
    return jsonify(team.to_dict()), 201

@team_bp.route('/<int:team_id>', methods=['GET'])
@jwt_required()
def get_team_details(team_id):
    """Get team details including members."""
    team = Team.query.get_or_404(team_id)
    data = team.to_dict()
    data['members'] = [{
        'id': m.id,
        'username': m.username,
        'email': m.email
    } for m in team.members]
    return jsonify(data)

@team_bp.route('/<int:team_id>/members', methods=['POST'])
@jwt_required()
def add_member(team_id):
    """Add a user to a team."""
    team = Team.query.get_or_404(team_id)
    data = request.get_json()
    
    user_id = data.get('user_id')
    username = data.get('username')
    
    user = None
    if user_id:
        user = User.query.get(user_id)
    elif username:
        user = User.query.filter_by(username=username).first()
        
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if user in team.members:
        return jsonify({'message': 'User already in team'}), 200
        
    team.members.append(user)
    db.session.commit()
    
    return jsonify({'message': f'User {user.username} added to team {team.name}'})

@team_bp.route('/<int:team_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(team_id, user_id):
    """Remove a user from a team."""
    team = Team.query.get_or_404(team_id)
    user = User.query.get_or_404(user_id)
    
    if user in team.members:
        team.members.remove(user)
        db.session.commit()
        
    return jsonify({'message': 'User removed from team'})

@team_bp.route('/<int:team_id>/invites', methods=['POST'])
@jwt_required()
def create_invitation(team_id):
    """Create a new invitation."""
    team = Team.query.get_or_404(team_id)
    current_user_id = get_jwt_identity()
    
    # Check if user is member (or admin)
    if not any(m.id == int(current_user_id) for m in team.members):
        return jsonify({'error': 'Permission denied'}), 403
        
    data = request.get_json() or {}
    email = data.get('email')
    
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=current_user_id,
        email=email,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.session.add(invitation)
    db.session.commit()
    
    invite_link = f"{request.host_url}?invite={invitation.token}"
    
    if email:
        EmailService.send_invitation_email(email, team.name, invite_link)
        
    return jsonify({
        'message': 'Invitation created',
        'link': invite_link,
        'invitation': invitation.to_dict()
    })

@team_bp.route('/invites/<token>', methods=['GET'])
def get_invitation(token):
    """Get invitation details."""
    invitation = TeamInvitation.query.filter_by(token=token).first_or_404()
    
    if invitation.status != 'pending':
        return jsonify({'error': 'Invitation is no longer valid'}), 400
        
    if invitation.expires_at and invitation.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invitation has expired'}), 400
        
    return jsonify(invitation.to_dict())

@team_bp.route('/invites/<token>/accept', methods=['POST'])
@jwt_required()
def accept_invitation(token):
    """Accept an invitation."""
    invitation = TeamInvitation.query.filter_by(token=token).first_or_404()
    
    if invitation.status != 'pending':
        return jsonify({'error': 'Invitation is no longer valid'}), 400
        
    if invitation.expires_at and invitation.expires_at < datetime.utcnow():
        return jsonify({'error': 'Invitation has expired'}), 400
        
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Add user to team
    team = Team.query.get(invitation.team_id)
    if user not in team.members:
        team.members.append(user)
        
    invitation.status = 'accepted'
    db.session.commit()
    
    return jsonify({
        'message': f'You have joined {team.name}',
        'team_id': team.id
    })
