import pytest
from api.models.target import Target

def test_bulk_create_target_assigns_user(client, auth_header, app):
    """
    Test that creating a target via the bulk endpoint assigns the current user as the owner.
    This reproduces the issue where targets were created without a user_id.
    """
    # 1. Create target via bulk endpoint
    response = client.post('/api/targets/bulk', json={
        'input': '192.168.1.200',
        'type': 'ip',
        'description': 'Bulk Created Target'
    }, headers=auth_header)
    
    assert response.status_code == 201
    target_id = response.json['id']
    
    # 2. Verify target exists in DB and has correct user_id
    with app.app_context():
        target = Target.query.get(target_id)
        assert target is not None
        # This assertion is expected to fail before the fix
        assert target.user_id is not None, "Target should have a user_id assigned"
        
    # 3. Verify target is listed in get_targets
    get_response = client.get('/api/targets/', headers=auth_header)
    assert get_response.status_code == 200
    
    target_ids = [t['id'] for t in get_response.json]
    assert target_id in target_ids, "Target should be visible to the user who created it"
