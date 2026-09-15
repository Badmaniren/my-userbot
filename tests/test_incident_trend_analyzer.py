import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json

from skills.incident_trend_analyzer import start_new, IncidentTrendAnalyzer
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestIncidentTrendAnalyzer(unittest.TestCase):

    def setUp(self):
        self.random_incident_id = uuid.uuid4().hex
        self.random_error_msg = f"error_{uuid.uuid4().hex}"
        self.random_module_name = f"module_{uuid.uuid4().hex}"
        self.random_raw = f"raw_{uuid.uuid4().hex}"
        self.random_patch = f"patch_{uuid.uuid4().hex}"

    def test_start_new_default_values(self):
        result = start_new()
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["incident_id"])
        self.assertIsNone(result["error"])
        self.assertIsNone(result["raw_result"])
        self.assertIsNone(result["patch_data"])

    def test_start_new_custom_values(self):
        success_flag = random.choice([True, False])
        result = start_new(
            success=success_flag,
            incident_id=self.random_incident_id,
            error=self.random_error_msg,
            raw_result=self.random_raw,
            patch_data=self.random_patch
        )
        self.assertEqual(result["incident_id"], self.random_incident_id)
        self.assertEqual(result["success"], success_flag)
        self.assertEqual(result["error"], self.random_error_msg)
        self.assertEqual(result["raw_result"], self.random_raw)
        self.assertEqual(result["patch_data"], self.random_patch)

    def test_incident_trend_analyzer_analyze_trends(self):
        analyzer = IncidentTrendAnalyzer()
        analysis = analyzer.analyze_trends(self.random_module_name)
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis["module_name"], self.random_module_name)
        self.assertEqual(analysis["status"], "analyzed")
        self.assertIn("trend", analysis)

    def test_trend_analyzer_and_recovery_flow(self):
        dashboard_gen = RecoveryDashboardGenerator()
        metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        incidents = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        reports = [{uuid.uuid4().hex: uuid.uuid4().hex}]
        
        dashboard_str = dashboard_gen.generate_dashboard(metrics, incidents, reports, format="json")
        self.assertIsInstance(dashboard_str, str)
        
        random_path = f"/tmp/{uuid.uuid4().hex}.json"
        
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            export_success = dashboard_gen.export_dashboard(dashboard_str, random_path)
            self.assertTrue(export_success)
            mock_file.assert_called_once_with(random_path, 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with(dashboard_str)

    def test_dashboard_generator_stream_parsing(self):
        dashboard_gen = RecoveryDashboardGenerator()
        payload_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "incident_id": self.random_incident_id
        }
        stream_bytes = io.BytesIO(json.dumps(payload_data).encode('utf-8'))
        
        parsed = dashboard_gen.parse_stream_data(stream_bytes)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed.get("incident_id"), self.random_incident_id)