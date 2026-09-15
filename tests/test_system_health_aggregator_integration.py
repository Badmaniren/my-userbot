import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_aggregator import SystemHealthAggregator, aggregate_system_health

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Critical error {random.randint(1000, 9999)}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}"
        self.incident_id = str(uuid.uuid4())
        self.audit_summary = {"status": "checked", "vulnerabilities": random.randint(0, 5)}
        self.metrics = {"cpu_load": random.uniform(10.0, 99.0), "memory_usage": random.randint(512, 4096)}

    def test_collect_and_aggregate_health_integration(self):
        result = self.aggregator.collect_and_aggregate_health(
            module_name=self.module_name,
            exception_msg=self.exception_msg,
            traceback_str=self.traceback_str,
            incident_id=self.incident_id,
            audit_summary=self.audit_summary,
            metrics=self.metrics
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_aggregation", result)
        self.assertIn("health_report", result)

        incident_agg = result["incident_aggregation"]
        health_rep = result["health_report"]

        self.assertIsInstance(incident_agg, dict)
        self.assertEqual(incident_agg.get("incident_id"), self.incident_id)
        self.assertEqual(incident_agg.get("module_name"), self.module_name)

        self.assertIsInstance(health_rep, dict)
        self.assertEqual(health_rep.get("metrics"), self.metrics)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            export_path = tmp.name

        try:
            export_result = self.aggregator.export_aggregated_health(health_rep, export_path)
            self.assertTrue(os.path.exists(export_path))
            self.assertGreater(os.path.getsize(export_path), 0)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_functional_aggregate_system_health_integration(self):
        exc = Exception(self.exception_msg)
        result = aggregate_system_health(
            module_name=self.module_name,
            exception=exc,
            traceback_str=self.traceback_str,
            incident_id=self.incident_id,
            audit_summary=self.audit_summary,
            metrics=self.metrics
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_summary", result)
        self.assertIn("health_report", result)

        incident_sum = result["incident_summary"]
        health_rep = result["health_report"]

        self.assertIsInstance(incident_sum, dict)
        self.assertIsInstance(health_rep, dict)
        self.assertEqual(health_rep.get("metrics"), self.metrics)

if __name__ == "__main__":
    unittest.main()