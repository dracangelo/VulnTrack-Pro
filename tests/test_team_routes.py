"""
Tests for team routes API endpoints.
"""
import pytest
from api.models.team import Team
from api.models.user import User
from api.models.invitation import TeamInvitation
from api.extensions import db
from datetime import datetime, timedelta


def test_get_teams(client, auth_headers):
    """Test getting teams for a user."""
    response = client.get('/api/teams/', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_create_team(client, auth_headers):
    """Test creating a new team."""
    team_data = {
        'name': 'Security Team',
        'description': 'Security testing team'
    }
    response = client.post('/api/teams/', json=team_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Security Team'
    assert data['description'] == 'Security testing team'
    assert 'id' in data


def test_create_team_missing_name(client, auth_headers):
    """Test creating team without name fails."""
    team_data = {'description': 'No name team'}
    response = client.post('/api/teams/', json=team_data, headers=auth_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_create_team_duplicate_name(client, auth_headers, test_user):
    """Test creating team with duplicate name fails."""
    # Create first team
    team = Team(name='Duplicate Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    # Try to create team with same name
    team_data = {'name': 'Duplicate Team'}
    response = client.post('/api/teams/', json=team_data, headers=auth_headers)
    assert response.status_code == 409
    data = response.get_json()
    assert 'error' in data


def test_get_team_details(client, auth_headers, test_user):
    """Test getting team details."""
    # Create team
    team = Team(name='Test Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    response = client.get(f'/api/teams/{team.id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Test Team'
    assert data['creator_id'] == test_user.id
    assert 'members' in data
    assert len(data['members']) == 1
    assert data['members'][0]['username'] == test_user.username


def test_add_member_by_user_id(client, auth_headers, test_user):
    """Test adding a member to team by user_id."""
    # Create team
    team = Team(name='Add Member Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    
    # Create another user
    new_user = User(username='newmember', email='new@test.com')
    new_user.set_password('password123')
    db.session.add(new_user)
    db.session.commit()
    
    # Add member
    response = client.post(
        f'/api/teams/{team.id}/members',
        json={'user_id': new_user.id},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    
    # Verify member was added
    team = Team.query.get(team.id)
    assert len(team.members) == 2


def test_add_member_by_username(client, auth_headers, test_user):
    """Test adding a member to team by username."""
    # Create team
    team = Team(name='Username Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    
    # Create another user
    new_user = User(username='userbyname', email='userbyname@test.com')
    new_user.set_password('password123')
    db.session.add(new_user)
    db.session.commit()
    
    # Add member by username
    response = client.post(
        f'/api/teams/{team.id}/members',
        json={'username': 'userbyname'},
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify member was added
    team = Team.query.get(team.id)
    assert len(team.members) == 2


def test_add_member_not_found(client, auth_headers, test_user):
    """Test adding non-existent user fails."""
    team = Team(name='Not Found Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    response = client.post(
        f'/api/teams/{team.id}/members',
        json={'user_id': 99999},
        headers=auth_headers
    )
    assert response.status_code == 404


def test_add_member_already_in_team(client, auth_headers, test_user):
    """Test adding user already in team."""
    team = Team(name='Already Member Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    response = client.post(
        f'/api/teams/{team.id}/members',
        json={'user_id': test_user.id},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'already in team' in data['message'].lower()


def test_remove_member_self(client, auth_headers, test_user):
    """Test user can remove themselves from team (leave)."""
    team = Team(name='Leave Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    response = client.delete(
        f'/api/teams/{team.id}/members/{test_user.id}',
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify user was removed
    team = Team.query.get(team.id)
    assert test_user not in team.members


def test_remove_member_by_creator(client, auth_headers, test_user):
    """Test team creator can remove other members."""
    # Create team
    team = Team(name='Remove Member Team', creator_id=test_user.id)
    team.members.append(test_user)
    
    # Create another user
    other_user = User(username='removeme', email='removeme@test.com')
    other_user.set_password('password123')
    team.members.append(other_user)
    db.session.add(team)
    db.session.add(other_user)
    db.session.commit()
    
    # Creator removes other user
    response = client.delete(
        f'/api/teams/{team.id}/members/{other_user.id}',
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify user was removed
    team = Team.query.get(team.id)
    assert other_user not in team.members
    assert test_user in team.members


def test_remove_member_permission_denied(client, test_user):
    """Test non-creator cannot remove other members."""
    # Create team with different creator
    creator = User(username='creator', email='creator@test.com')
    creator.set_password('password123')
    db.session.add(creator)
    
    team = Team(name='Permission Team', creator_id=creator.id)
    team.members.append(creator)
    team.members.append(test_user)
    
    # Create third user
    other_user = User(username='other', email='other@test.com')
    other_user.set_password('password123')
    team.members.append(other_user)
    db.session.add(team)
    db.session.add(other_user)
    db.session.commit()
    
    # test_user (not creator) tries to remove other_user
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(test_user.id))
    headers = {'Authorization': f'Bearer {token}'}
    
    response = client.delete(
        f'/api/teams/{team.id}/members/{other_user.id}',
        headers=headers
    )
    assert response.status_code == 403
    data = response.get_json()
    assert 'permission denied' in data['error'].lower()


def test_create_invitation(client, auth_headers, test_user):
    """Test creating team invitation."""
    team = Team(name='Invite Team', creator_id=test_user.id)
    team.members.append(test_user)
    db.session.add(team)
    db.session.commit()
    
    response = client.post(
        f'/api/teams/{team.id}/invites',
        json={'email': 'invite@test.com'},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'link' in data
    assert 'invitation' in data
    assert data['invitation']['team_id'] == team.id


def test_create_invitation_permission_denied(client, test_user):
    """Test non-member cannot create invitation."""
    # Create team without test_user
    creator = User(username='invitecreator', email='invitecreator@test.com')
    creator.set_password('password123')
    db.session.add(creator)
    
    team = Team(name='No Permission Team', creator_id=creator.id)
    team.members.append(creator)
    db.session.add(team)
    db.session.commit()
    
    # test_user tries to create invitation
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(test_user.id))
    headers = {'Authorization': f'Bearer {token}'}
    
    response = client.post(
        f'/api/teams/{team.id}/invites',
        json={'email': 'test@test.com'},
        headers=headers
    )
    assert response.status_code == 403


def test_get_invitation(client, test_user):
    """Test getting invitation details."""
    team = Team(name='Get Invite Team', creator_id=test_user.id)
    db.session.add(team)
    db.session.commit()
    
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=test_user.id,
        email='getinvite@test.com',
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(invitation)
    db.session.commit()
    
    response = client.get(f'/api/teams/invites/{invitation.token}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['team_id'] == team.id
    assert data['status'] == 'pending'


def test_get_invitation_expired(client, test_user):
    """Test getting expired invitation fails."""
    team = Team(name='Expired Team', creator_id=test_user.id)
    db.session.add(team)
    db.session.commit()
    
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=test_user.id,
        email='expired@test.com',
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
    )
    db.session.add(invitation)
    db.session.commit()
    
    response = client.get(f'/api/teams/invites/{invitation.token}')
    assert response.status_code == 400
    data = response.get_json()
    assert 'expired' in data['error'].lower()


def test_accept_invitation(client, auth_headers, test_user):
    """Test accepting team invitation."""
    # Create team
    creator = User(username='acceptcreator', email='acceptcreator@test.com')
    creator.set_password('password123')
    db.session.add(creator)
    
    team = Team(name='Accept Team', creator_id=creator.id)
    team.members.append(creator)
    db.session.add(team)
    db.session.commit()
    
    # Create invitation
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=creator.id,
        email=test_user.email,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(invitation)
    db.session.commit()
    
    # Accept invitation
    response = client.post(
        f'/api/teams/invites/{invitation.token}/accept',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'joined' in data['message'].lower()
    assert data['team_id'] == team.id
    
    # Verify user was added to team
    team = Team.query.get(team.id)
    assert test_user.id in [m.id for m in team.members]
    
    # Verify invitation status changed
    invitation = TeamInvitation.query.get(invitation.id)
    assert invitation.status == 'accepted'


def test_accept_invitation_already_accepted(client, auth_headers, test_user):
    """Test accepting already accepted invitation fails."""
    team = Team(name='Already Accepted Team', creator_id=test_user.id)
    db.session.add(team)
    db.session.commit()
    
    invitation = TeamInvitation(
        team_id=team.id,
        inviter_id=test_user.id,
        email='already@test.com',
        expires_at=datetime.utcnow() + timedelta(days=7),
        status='accepted'
    )
    db.session.add(invitation)
    db.session.commit()
    
    response = client.post(
        f'/api/teams/invites/{invitation.token}/accept',
        headers=auth_headers
    )
    assert response.status_code == 400
    data = response.get_json()
    assert 'no longer valid' in data['error'].lower()
