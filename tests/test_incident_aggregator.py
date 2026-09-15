import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.incident_aggregator import IncidentAggregator

class TestIncidentAggregator(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.rand_incident_id = str(uuid.uuid4())
        self.rand_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.rand_error_msg = f"error_{uuid.uuid4().hex[:6]}"
        self.rand_metric_value = random.randint(1, 1000)

    def test_aggregate_incident_metrics_success(self):
        raw_metrics = {
            "incident_id": self.rand_incident_id,
            "module": self.rand_module_name,
            "error": self.rand_error_msg,
            "load_time": self.rand_metric_value
        }
        
        with patch("skills.incident_aggregator.IncidentAggregator._fetch_external_telemetry") as mock_fetch:
            mock_fetch.return_value = raw_metrics
            result = self.aggregator.aggregate_metrics(self.rand_incident_id)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.rand_incident_id)
            self.assertEqual(result.get("module"), self.rand_module_name)
            self.assertIn("analyzed_at", result)

    def test_process_pipeline_results_chaos(self):
        pipeline_stream = io.BytesIO(f"INCIDENT_ID:{self.rand_incident_id}|STATUS:FAILED|ERR:{self.rand_error_msg}".encode('utf-8'))
        
        result = self.aggregator.process_stream(pipeline_stream)
        
        self.assertIsNotNone(result)
        self.assertIn(self.rand_incident_id, result.get("processed_ids", []))
        self.assertEqual(result.get("error_caught"), self.rand_error_msg)

    def test_build_summary_analytics(self):
        mock_history = [
            {"id": str(uuid.uuid4()), "module": self.rand_module_name, "success": False},
            {"id": str(uuid.uuid4()), "module": self.rand_module_name, "success": True}
        ]
        
        with patch("skills.incident_aggregator.ErrorRecoveryHub") as mock_hub_class:
            mock_hub_instance = mock_hub_class.return_value
            mock_hub_instance.get_incident_history.return_value = mock_history
            
            summary = self.aggregator.build_analytics(self.rand_module_name)
            
            self.assertIsInstance(summary, dict)
            self.assertEqual(summary.get("total_incidents"), 2)
            self.assertEqual(summary.get("module"), self.rand_module_name)
            self.assertTrue(0.0 <= summary.get("success_rate", -1.0) <= 100.0)

    def test_export_aggregated_report_format(self):
        export_payload = {
            "report_id": uuid.uuid4().hex,
            "target_module": self.rand_module_name,
            "criticality": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }
        
        output_format = random.choice(["json", "csv", "xml"])
        report_str = self.aggregator.export_summary(export_payload, format=output_format)
        
        self.assertIsInstance(report_str, str)
        self.assertIn(export_payload["report_id"], report_str)
        self.assertIn(self.rand_module_name, report_str)

if __name__ == "__main__":
    unittest.main()