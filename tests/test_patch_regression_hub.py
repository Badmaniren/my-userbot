import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.patch_regression_hub import AnomalyAuditHub, start_new


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/repo/{uuid.uuid4().hex}"
        self.log_path_val = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold_val = round(random.uniform(0.1, 0.9), 2)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val
        )

    def test_init_sets_attributes_correctly(self):
        self.assertEqual(self.hub.repo_path, self.repo_path_val)
        self.assertEqual(self.hub.log_path, self.log_path_val)
        self.assertEqual(self.hub.threshold, self.threshold_val)
        self.assertIsNotNone(self.hub.logger)
        self.assertIsNotNone(self.hub.inspector)

    def test_log_anomaly_adds_to_internal_storage(self):
        source_val = f"src_{uuid.uuid4().hex[:8]}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = f"detail_{uuid.uuid4().hex}"
        telemetry_val = {uuid.uuid4().hex: random.randint(1, 100)}

        self.hub.log_anomaly(
            source=source_val,
            severity=severity_val,
            details=details_val,
            telemetry_snapshot=telemetry_val
        )

        self.assertTrue(hasattr(self.hub.logger, "anomalies"))
        anomalies = self.hub.logger.anomalies
        self.assertTrue(any(a["source"] == source_val and a["details"] == details_val for a in anomalies))

    def test_aggregate_and_report_returns_expected_structure(self):
        metric_name_val = f"metric_{uuid.uuid4().hex[:6]}"
        value_val = round(random.uniform(1.0, 100.0), 2)

        source_val = f"src_{uuid.uuid4().hex[:8]}"
        self.hub.log_anomaly(source=source_val, severity="LOW", details=uuid.uuid4().hex)

        report = self.hub.aggregate_and_report(metric_name=metric_name_val, value=value_val)

        self.assertIsInstance(report, dict)
        self.assertTrue(report.get("aggregated"))
        self.assertEqual(report.get("score"), value_val)
        self.assertEqual(report.get("metric_name"), metric_name_val)
        self.assertGreaterEqual(report.get("total_anomalies"), 1)

    def test_generate_final_report_returns_correct_fields(self):
        source_val = f"src_{uuid.uuid4().hex[:8]}"
        self.hub.log_anomaly(source=source_val, severity="HIGH", details=uuid.uuid4().hex)

        report = self.hub.generate_final_report()

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("status"), "verified")
        self.assertEqual(report.get("code"), "success")
        self.assertGreaterEqual(report.get("anomalies_count"), 1)

    def test_start_new_with_stream_source(self):
        token_val = uuid.uuid4().hex
        repo_val = f"/path/{uuid.uuid4().hex}"
        input_data = {
            "stream_source": True,
            "repo_path": repo_val,
            "token": token_val
        }

        mock_analysis_result = {"status": "analyzed", "data": uuid.uuid4().hex}

        with patch("skills.patch_regression_hub.GitInspector") as mock_git_inspector_cls:
            mock_inspector_instance = mock_git_inspector_cls.return_value
            mock_inspector_instance.analyze_repository.return_value = mock_analysis_result

            result = start_new(input_data)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("token"), token_val)
            mock_git_inspector_cls.assert_called_once_with(repo_path=repo_val)
            mock_inspector_instance.analyze_repository.assert_called_once()

    def test_start_new_with_payload_id(self):
        payload_id_val = f"payload_{uuid.uuid4().hex[:8]}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH"])
        target_val = f"target_{uuid.uuid4().hex[:6]}"
        error_rate_val = round(random.uniform(0.0, 1.0), 3)

        input_data = {
            "payload_id": payload_id_val,
            "severity_level": severity_val,
            "target": target_val,
            "error_rate": error_rate_val
        }

        result = start_new(input_data)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("aggregated"))
        self.assertEqual(result.get("score"), error_rate_val)
        self.assertEqual(result.get("metric_name"), target_val)

    def test_start_new_default_flow(self):
        target_val = f"metric_{uuid.uuid4().hex[:6]}"
        numeric_metric_val = round(random.uniform(10.0, 50.0), 2)
        random_str_key = f"key_{uuid.uuid4().hex[:6]}"
        random_str_val = f"val_{uuid.uuid4().hex}"

        input_data = {
            "target": target_val,
            "numeric_metric": numeric_metric_val,
            random_str_key: random_str_val
        }

        result = start_new(input_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "verified")
        self.assertEqual(result.get("code"), "success")
        self.assertGreaterEqual(result.get("anomalies_count"), 1)


if __name__ == "__main__":
    unittest.main()