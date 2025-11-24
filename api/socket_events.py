from flask_socketio import emit, join_room, leave_room
from api.extensions import socketio

@socketio.on('connect', namespace='/scan-progress')
def handle_connect():
    """Handle client connection to scan progress namespace"""
    print('Client connected to scan-progress namespace')
    emit('connected', {'message': 'Connected to scan progress updates'})

@socketio.on('disconnect', namespace='/scan-progress')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected from scan-progress namespace')

@socketio.on('subscribe_scan', namespace='/scan-progress')
def handle_subscribe(data):
    """Subscribe to updates for a specific scan"""
    scan_id = data.get('scan_id')
    if scan_id:
        room = f'scan_{scan_id}'
        join_room(room)
        emit('subscribed', {'scan_id': scan_id, 'room': room})
        print(f'Client subscribed to scan {scan_id}')

@socketio.on('unsubscribe_scan', namespace='/scan-progress')
def handle_unsubscribe(data):
    """Unsubscribe from scan updates"""
    scan_id = data.get('scan_id')
    if scan_id:
        room = f'scan_{scan_id}'
        leave_room(room)
        emit('unsubscribed', {'scan_id': scan_id})
        print(f'Client unsubscribed from scan {scan_id}')
