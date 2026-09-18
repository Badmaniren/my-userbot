import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import json
from skills.incident_forensic_collector import ForensicCollector

class TestIncidentForensicCollector(unittest.TestCase):

    def setUp(self):
        self.collector = ForensicCollector()

    def test_start_new_incident_collection_flow(self):
        incident_id = uuid.uuid4().hex
        source_url = f"https://{uuid.uuid4().hex}.internal/{uuid.uuid4().hex}"
        expected_payload = {
            "incident_id": incident_id,
            "telemetry_source": source_url,
            "timestamp": random.randint(1000000000, 9999999999)
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(expected_payload).encode('utf-8')

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.collector.start_new(incident_id, source_url)
            
            mock_get.assert_called_once_with(source_url, timeout=unittest.mock.ANY)
            self.assertEqual(result['incident_id'], incident_id)
            self.assertEqual(result['telemetry_source'], source_url)

    def test_start_new_handles_malformed_telemetry(self):
        incident_id = uuid.uuid4().hex
        source_url = f"https://{uuid.uuid4().hex}.log-streamer.local"
        random_garbage = ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.content = random_garbage
            
            with self.assertRaises(ValueError):
                self.collector.start_new(incident_id, source_url)

    def test_start_new_persistence_integrity(self):
        incident_id = uuid.uuid4().hex
        file_path = f"/tmp/{uuid.uuid4().hex}.forensic"
        telemetry_data = {
            "node": uuid.uuid4().hex,
            "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
            "entropy": random.random()
        }

        with patch('builtins.open', unittest.mock.mock_open()) as mocked_file:
            with patch('json.dump') as mock_json_dump:
                self.collector.start_new(incident_id, "http://localhost", save_path=file_path, data=telemetry_data)
                
                mocked_file.assert_called_once_with(file_path, 'w')
                args, _ = mock_json_dump.call_args
                self.assertEqual(args[0]['incident_id'], incident_id)
                self.assertEqual(args[0]['entropy'], telemetry_data['entropy'])

    def test_start_new_network_failure_resilience(self):
        incident_id = uuid.uuid4().hex
        source_url = f"https://{uuid.uuid4().hex}.fail"

        with patch('requests.get', side_effect=Exception("Connection Timeout")):
            with self.assertRaises(ConnectionError):
                self.collector.start_new(incident_id, source_url)

    def test_start_new_stream_processing(self):
        incident_id = uuid.uuid4().hex
        stream_content = b"LOG_START:" + uuid.uuid4().hex.encode() + b":LOG_END"
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raw = io.BytesIO(stream_content)
            
            result = self.collector.start_new(incident_id, "http://stream.internal")
            
            self.assertIn(incident_id, result['metadata'])
            self.assertTrue(result['stream_processed'])

if __name__ == '__main__':
    unittest.main()