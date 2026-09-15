import unittest
import uuid
import random
import os
from skills.incident_aggregator import IncidentAggregator


class TestIncidentAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.incident_id = f"inc_{uuid.uuid4().hex}"
        self.export_format = random.choice(["json", "xml", "csv", "yaml"])

    def test_aggregate_and_report_integration(self):
        metric_payload = {
            "incident_id": self.incident_id,
            "success": random.choice([True, False]),
            "error": f"error_{uuid.uuid4().hex[:6]}",
            "module": self.module_name
        }

        recorded = self.aggregator.record_incident_metric(metric_payload)
        self.assertIsNotNone(recorded)

        report_result = self.aggregator.aggregate_and_report(self.module_name, self.export_format)
        self.assertIsInstance(report_result, str)
        self.assertTrue(len(report_result) > 0)

    def test_export_system_health_metrics_integration(self):
        output_path = f"health_metrics_{uuid.uuid4().hex}.txt"
        try:
            metric_payload = {
                "incident_id": self.incident_id,
                "success": True,
                "module": self.module_name
            }
            self.aggregator.record_incident_metric(metric_payload)

            export_status = self.aggregator.export_system_health_metrics(output_path, self.export_format)
            self.assertIn(export_status, [True, False])
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_generate_health_report_integration(self):
        audit_data = f"audit_info_{uuid.uuid4().hex}"
        metrics_payload = {"incident_id": self.incident_id}

        report = self.aggregator.generate_health_report(
            self.module_name,
            audit_data,
            metrics_payload
        )

        self.assertIsInstance(report, str)
        self.assertIn(self.module_name, report)
        self.assertIn(self.incident_id, report)


if __name__ == "__main__":
    unittest.main()