import unittest
from unittest.mock import patch, mock_open
import uuid
import json
import random
import io
import sys
from types import ModuleType

from skills.incident_post_mortem_generator import IncidentPostMortemGenerator, generate_post_mortem

class TestIncidentPostMortemGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = IncidentPostMortemGenerator()
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.root_cause = uuid.uuid4().hex
        self.resolution_steps = uuid.uuid4().hex
        self.file_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.telemetry_path = f"/tmp/{uuid.uuid4().hex}.log"

    def test_generate_report_success(self):
        escalation_data = {
            "incident_id": self.incident_id,
            "severity": self.severity
        }
        recovery_data = {
            "root_cause": self.root_cause,
            "resolution_steps": self.resolution_steps
        }
        report = self.generator.generate_report(escalation_data, recovery_data)
        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertEqual(report["severity"], self.severity)
        self.assertEqual(report["root_cause"], self.root_cause)
        self.assertEqual(report["resolution_steps"], self.resolution_steps)
        self.assertIn("post_mortem_id", report)

    def test_generate_report_missing_fields(self):
        bad_escalation = {"incident_id": self.incident_id}
        recovery_data = {
            "root_cause": self.root_cause,
            "resolution_steps": self.resolution_steps
        }
        with self.assertRaises(ValueError):
            self.generator.generate_report(bad_escalation, recovery_data)

    def test_export_report(self):
        report_data = {
            "post_mortem_id": uuid.uuid4().hex,
            "incident_id": self.incident_id,
            "severity": self.severity,
            "root_cause": self.root_cause,
            "resolution_steps": self.resolution_steps
        }
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            result = self.generator.export_report(report_data, self.file_path)
            self.assertTrue(result)
            mock_file.assert_called_once_with(self.file_path, "wb")
            handle = mock_file()
            handle.write.assert_called_once()

    def test_extract_metrics_from_telemetry(self):
        metric_key = uuid.uuid4().hex
        metric_val = uuid.uuid4().hex
        telemetry_content = f"{metric_key}: {metric_val}\n"
        with patch("builtins.open", mock_open(read_data=telemetry_content)):
            metrics = self.generator.extract_metrics_from_telemetry(self.telemetry_path)
            self.assertIn(metric_key, metrics)
            self.assertEqual(metrics[metric_key], metric_val)

    def test_compile_full_post_mortem(self):
        escalation_data = {
            "incident_id": self.incident_id,
            "severity": self.severity
        }
        recovery_data = {
            "root_cause": self.root_cause,
            "resolution_steps": self.resolution_steps
        }
        metric_key = uuid.uuid4().hex
        metric_val = uuid.uuid4().hex
        telemetry_content = f"{metric_key}: {metric_val}\n"
        with patch("builtins.open", mock_open(read_data=telemetry_content)):
            report = self.generator.compile_full_post_mortem(escalation_data, recovery_data, self.telemetry_path)
            self.assertEqual(report["incident_id"], self.incident_id)
            self.assertIn("telemetry_metrics", report)
            self.assertEqual(report["telemetry_metrics"][metric_key], metric_val)

    def test_generate_post_mortem_function(self):
        payload = {
            "incident_id": self.incident_id,
            "aggregation": {},
            "escalation": {"severity": self.severity},
            "recovery": {
                "root_cause": self.root_cause,
                "action": self.resolution_steps
            },
            "output_path": self.file_path
        }
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            res = generate_post_mortem(payload)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["incident_id"], self.incident_id)
            self.assertEqual(res["report"]["severity"], self.severity)
            self.assertEqual(res["report"]["root_cause"], self.root_cause)
            self.assertEqual(res["report"]["resolution_steps"], self.resolution_steps)

if __name__ == "__main__":
    unittest.main()