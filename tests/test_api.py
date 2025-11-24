def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'healthy'}

def test_create_target(client):
    response = client.post('/api/targets/', json={
        'name': 'Test Target',
        'ip_address': '127.0.0.1',
        'description': 'Test Description'
    })
    assert response.status_code == 201
    assert response.json['message'] == 'Target created'
    
    # Verify it exists
    response = client.get('/api/targets/')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Target'

def test_create_ticket(client):
    # Create ticket
    response = client.post('/api/tickets/', json={
        'title': 'Test Ticket',
        'priority': 'high'
    })
    assert response.status_code == 201
    
    # Verify
    response = client.get('/api/tickets/')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['title'] == 'Test Ticket'
    assert response.json[0]['priority'] == 'high'

def test_scan_flow(client):
    # 1. Create Target
    res_target = client.post('/api/targets/', json={
        'name': 'Scan Target',
        'ip_address': '127.0.0.1'
    })
    target_id = res_target.json['id']
    
    # 2. Create Scan (Mocking the actual scan execution would be ideal, but for now we test the endpoint)
    # Since we use threading, the scan runs in background. 
    # We just check if endpoint accepts it.
    res_scan = client.post('/api/scans/', json={
        'target_id': target_id,
        'scan_type': 'nmap',
        'args': '-sP' # Ping scan for speed
    })
    assert res_scan.status_code == 201
    scan_id = res_scan.json['scan_id']
    
    # 3. Check Status
    res_status = client.get(f'/api/scans/{scan_id}')
    assert res_status.status_code == 200
    assert res_status.json['status'] in ['pending', 'running', 'completed', 'failed']
