import unittest
import io
import json
import uuid
import random
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock
from skills.incident_aggregator import IncidentAggregator

class TestIncidentAggregator(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()

    def test_aggregate_metrics_with_id_mocking_network(self):
        incident_id = uuid.uuid4().hex
        mock_data = {
            "module": uuid.uuid4().hex,
            "error": uuid.uuid4().hex,
            "load_time": random.uniform(0.1, 10.0)
        }

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            result = self.aggregator.aggregate_metrics(incident_id)
            
            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["module"], mock_data["module"])
            self.assertEqual(result["error"], mock_data["error"])
            self.assertEqual(result["load_time"], mock_data["load_time"])
            mock_get.assert_called_once()

    def test_aggregate_metrics_list_input(self):
        count = random.randint(1, 5)
        incidents = [{"id": uuid.uuid4().hex} for _ in range(count)]
        
        result = self.aggregator.aggregate_metrics(incidents)
        
        self.assertEqual(len(result["incidents"]), count)
        self.assertIn("analyzed_at", result)
        self.assertEqual(result["incidents"], incidents)

    def test_process_stream_parsing(self):
        incident_id = uuid.uuid4().hex
        error_msg = uuid.uuid4().hex
        stream_content = f"INCIDENT_ID:{incident_id}|ERR:{error_msg}".encode('utf-8')
        stream = io.BytesIO(stream_content)
        
        result = self.aggregator.process_stream(stream)
        
        self.assertIn(incident_id, result["processed_ids"])
        self.assertEqual(result["error_caught"], error_msg)

    def test_build_analytics_logic(self):
        module_name = uuid.uuid4().hex
        total = random.randint(10, 20)
        success = random.randint(0, total)
        history = [{"success": True} for _ in range(success)] + [{"success": False} for _ in range(total - success)]
        
        with patch('skills.incident_aggregator.ErrorRecoveryHub') as mock_hub_class:
            mock_hub = mock_hub_class.return_value
            mock_hub.get_incident_history.return_value = history
            
            result = self.aggregator.build_analytics(module_name)
            
            self.assertEqual(result["module"], module_name)
            self.assertEqual(result["total_incidents"], total)
            expected_rate = (success / total) * 100.0 if total > 0 else 0.0
            self.assertEqual(result["success_rate"], expected_rate)

    def test_export_summary_formats(self):
        payload = {
            "report_id": uuid.uuid4().hex,
            "target_module": uuid.uuid4().hex,
            "criticality": random.choice(["low", "medium", "high"])
        }
        
        # Test JSON
        json_out = self.aggregator.export_summary(payload, format="json")
        self.assertEqual(json.loads(json_out), payload)
        
        # Test XML
        xml_out = self.aggregator.export_summary(payload, format="xml")
        root = ET.fromstring(xml_out)
        for k, v in payload.items():
            self.assertEqual(root.find(k).text, str(v))
            
        # Test Default (CSV-like)
        csv_out = self.aggregator.export_summary(payload, format="txt")
        self.assertIn(payload["report_id"], csv_out)
        self.assertIn(payload["target_module"], csv_out)

if __name__ == '__main__':
    unittest.main()