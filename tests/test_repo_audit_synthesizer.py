import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skills.repo_audit_synthesizer import start_new


class TestRepoAuditSynthesizer(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.random_output_dir = f"/output/{uuid.uuid4().hex}"
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_value = random.randint(100, 9999)
        self.random_security_flag = random.choice([True, False])
        self.random_performance_score = round(random.uniform(0.1, 99.9), 2)
        self.random_health_status = random.choice(["EXCELLENT", "CRITICAL", "WARNING", "OPTIMAL"])

    def test_start_new_success_synthesis(self):
        mock_payload = {
            "repository": self.random_repo_path,
            "security_metric": {self.random_metric_key: self.random_metric_value},
            "security_flag": self.random_security_flag,
            "performance_score": self.random_performance_score,
            "health_status": self.random_health_status
        }

        with patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor, \
             patch("skills.repo_audit_synthesizer.repo_performance_profiler_pipeline") as mock_perf, \
             patch("skills.repo_audit_synthesizer.vulnerability_analyzer") as mock_vuln, \
             patch("skills.repo_audit_synthesizer.repo_health_diagnostic") as mock_health:

            mock_auditor.scan.return_value = {"repo_path": self.random_repo_path, "status": "scanned"}
            mock_perf.run_profiler.return_value = {"score": self.random_performance_score}
            mock_vuln.analyze.return_value = {"secure": self.random_security_flag, "metric": {self.random_metric_key: self.random_metric_value}}
            mock_health.diagnose.return_value = {"health": self.random_health_status}

            result = start_new(self.random_repo_path, output_dir=self.random_output_dir)

            self.assertIsInstance(result, dict)
            self.assertIn("synthesis_id", result)
            self.assertEqual(result["repository"], self.random_repo_path)
            self.assertEqual(result["performance"]["score"], self.random_performance_score)
            self.assertEqual(result["vulnerability"]["metric"][self.random_metric_key], self.random_metric_value)
            self.assertEqual(result["health"]["health"], self.random_health_status)

            mock_auditor.scan.assert_called_once_with(self.random_repo_path)
            mock_perf.run_profiler.assert_called_once_with(self.random_repo_path)
            mock_vuln.analyze.assert_called_once_with(self.random_repo_path)
            mock_health.diagnose.assert_called_once_with(self.random_repo_path)

    def test_start_new_handles_exceptions_gracefully(self):
        random_error_msg = "".join(random.choices(string.ascii_letters + string.digits, k=16))

        with patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor:
            mock_auditor.scan.side_effect = Exception(random_error_msg)

            result = start_new(self.random_repo_path)

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertIn(random_error_msg, result["error"])
            self.assertEqual(result.get("repository"), self.random_repo_path)

    def test_start_new_with_stream_io_integration(self):
        random_stream_data = f"AUDIT_TARGET::{uuid.uuid4().hex}::SCORE::{random.randint(1, 100)}".encode('utf-8')
        mock_bytes_io = io.BytesIO(random_stream_data)

        with patch("skills.repo_audit_synthesizer.repo_reporter") as mock_reporter, \
             patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor:

            mock_auditor.scan.return_value = {"stream_processed": True}
            mock_reporter.export_stream.return_value = mock_bytes_io

            result = start_new(self.random_repo_path, export_stream=True)

            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("stream_processed"))
            
            exported_stream = mock_reporter.export_stream()
            read_data = exported_stream.read()
            self.assertEqual(read_data, random_stream_data)

    def test_start_new_validates_aggregated_metrics(self):
        random_threshold = random.randint(500, 1500)
        random_val_1 = random.randint(1, random_threshold)
        random_val_2 = random.randint(1, random_threshold)

        with patch("skills.repo_audit_synthesizer.repo_security_gateway") as mock_sec_gate, \
             patch("skills.repo_audit_synthesizer.repo_auditor") as mock_auditor:

            mock_auditor.scan.return_value = {"metrics": [random_val_1, random_val_2]}
            mock_sec_gate.evaluate.return_value = {
                "passed": (random_val_1 + random_val_2) < (random_threshold * 2),
                "threshold": random_threshold
            }

            result = start_new(self.random_repo_path)

            self.assertIsInstance(result, dict)
            self.assertIn("security_evaluation", result)
            self.assertTrue(result["security_evaluation"]["passed"])
            self.assertEqual(result["security_evaluation"]["threshold"], random_threshold)
            mock_sec_gate.evaluate.assert_called_once()