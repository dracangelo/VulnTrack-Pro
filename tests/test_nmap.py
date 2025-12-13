import pytest
from unittest.mock import patch, MagicMock, mock_open
from api.services.nmap_realtime_parser import NmapRealtimeParser
from api.services.nmap_service import NmapService

class TestNmapRealtimeParser:
    @pytest.fixture
    def parser(self):
        return NmapRealtimeParser()

    @patch('subprocess.Popen')
    @patch('tempfile.mkstemp')
    @patch('os.close')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_scan_target_success(self, mock_exists, mock_remove, mock_close, mock_mkstemp, mock_popen, parser):
        # Mock temp file
        mock_mkstemp.return_value = (1, '/tmp/test.xml')
        mock_exists.return_value = True
        
        # Mock subprocess
        process_mock = MagicMock()
        process_mock.stdout.readline.side_effect = [
            'Starting Nmap 7.92 at 2023-10-27 10:00 UTC\n',
            'Nmap scan report for localhost (127.0.0.1)\n',
            'Host is up (0.000010s latency).\n',
            'PORT   STATE SERVICE VERSION\n',
            '80/tcp open  http    Apache httpd 2.4.49\n',
            'Nmap done: 1 IP address (1 host up) scanned in 0.50 seconds\n',
            ''
        ]
        process_mock.wait.return_value = 0
        mock_popen.return_value = process_mock
        
        # Mock XML parsing (since we mock the file creation, we need to mock _parse_xml_results or the file read)
        # Easier to mock _parse_xml_results directly if we want to test the flow, 
        # OR mock ET.parse. Let's mock _parse_xml_results to simplify this test of the main loop.
        with patch.object(parser, '_parse_xml_results') as mock_parse_xml:
            mock_parse_xml.return_value = {'hosts': [{'host': '127.0.0.1', 'ports': []}]}
            
            results = parser.scan_target('127.0.0.1', '-F', 'scan_123', None)
            
            assert results['hosts'][0]['host'] == '127.0.0.1'
            assert mock_popen.called
            # Verify arguments
            args, _ = mock_popen.call_args
            cmd = args[0]
            assert 'nmap' in cmd
            assert '127.0.0.1' in cmd
            assert '-oX' in ' '.join(cmd)

    def test_parse_line_progress(self, parser):
        scan_data = {'hosts': [], 'ports': [], 'raw_output': '', 'discovered_hosts': 0, 'open_ports': 0}
        
        # Mock _emit_progress
        parser._emit_progress = MagicMock()
        
        parser._parse_line('About 45.67% done', scan_data, 'scan_1', None)
        
        parser._emit_progress.assert_called_with('scan_1', 45, 'Scanning in progress...', None)

    def test_parse_line_port(self, parser):
        scan_data = {'hosts': [], 'ports': [], 'raw_output': '', 'discovered_hosts': 0, 'open_ports': 0}
        
        # Mock _emit_port_discovered
        parser._emit_port_discovered = MagicMock()
        
        parser._parse_line('80/tcp   open  http', scan_data, 'scan_1', None)
        
        assert len(scan_data['ports']) == 1
        assert scan_data['ports'][0]['port'] == 80
        assert scan_data['ports'][0]['service'] == 'http'
        parser._emit_port_discovered.assert_called()

class TestNmapService:
    @patch('nmap.PortScanner')
    def test_scan_target(self, mock_scanner_cls):
        mock_scanner = mock_scanner_cls.return_value
        mock_scanner.all_hosts.return_value = ['127.0.0.1']
        mock_scanner.__getitem__.return_value = {'tcp': {80: {'state': 'open', 'name': 'http'}}}
        
        service = NmapService()
        result = service.scan_target('127.0.0.1')
        
        assert result['tcp'][80]['name'] == 'http'
        mock_scanner.scan.assert_called()

    def test_normalize_results(self):
        service = NmapService()
        raw_data = {
            'tcp': {
                80: {
                    'state': 'open',
                    'name': 'http',
                    'product': 'Apache',
                    'version': '2.4',
                    'cpe': 'cpe:/a:apache:http_server:2.4',
                    'script': {}
                }
            }
        }
        
        normalized = service.normalize_results(raw_data)
        assert len(normalized) == 1
        assert normalized[0]['port'] == 80
        assert normalized[0]['service'] == 'http'
        assert normalized[0]['product'] == 'Apache'
