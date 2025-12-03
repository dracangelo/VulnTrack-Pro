import unittest
from unittest.mock import MagicMock, patch
from api.services.nmap_realtime_parser import NmapRealtimeParser

class TestNmapParserLogs(unittest.TestCase):
    def setUp(self):
        self.parser = NmapRealtimeParser()

    @patch('api.extensions.socketio')
    def test_emit_log(self, mock_socketio):
        # Test _emit_log directly
        scan_id = 123
        message = "Test log message"
        app_context = MagicMock()
        
        self.parser._emit_log(scan_id, message, app_context)
        
        mock_socketio.emit.assert_called_with(
            'scan_log',
            {
                'scan_id': scan_id,
                'message': message,
                'timestamp': unittest.mock.ANY
            },
            room=f'scan_{scan_id}',
            namespace='/scan-progress'
        )

    @patch('api.extensions.socketio')
    def test_parse_line_emits_log(self, mock_socketio):
        # Test that _parse_line calls _emit_log
        scan_id = 123
        line = "Discovered open port 80/tcp on 192.168.1.1"
        scan_data = {'hosts': [], 'ports': [], 'discovered_hosts': 0, 'open_ports': 0}
        app_context = MagicMock()
        
        self.parser._parse_line(line, scan_data, scan_id, app_context)
        
        # Check if scan_log was emitted
        args, kwargs = mock_socketio.emit.call_args
        self.assertEqual(args[0], 'scan_log')
        self.assertEqual(kwargs['namespace'], '/scan-progress')
        self.assertEqual(kwargs['room'], f'scan_{scan_id}')
        self.assertEqual(args[1]['message'], line)

if __name__ == '__main__':
    unittest.main()
