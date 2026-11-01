import unittest
from unittest.mock import patch
import uuid
import random
import io
from skills.patch_regression_hub import AnomalyAuditHub, start_new


class TestAnomalyAuditHubAndRegressionHub(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}"
        self.log_path_val = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold_val = random.uniform(0.1, 0.9)
        self.hub = AnomalyAuditHub(repo_path=self.repo_path_val, log_path=self.log_path_val, threshold=self.threshold_val)

    def test_init_sets_attributes(self):
        rnd_repo = f"/var/repo_{uuid.uuid4().hex}"
        rnd_log = f"/var/log_{uuid.uuid4().hex}.log"
        rnd_thresh = random.random()
        hub_instance = AnomalyAuditHub(repo_path=rnd_repo, log_path=rnd_log, threshold=rnd_thresh)
        self.assertEqual(hub_instance.repo_path, rnd_repo)
        self.assertEqual(hub_instance.log_path, rnd_log)
        self.assertEqual(hub_instance.threshold, rnd_thresh)
        self.assertIsNotNone(hub_instance.logger)
        self.assertIsNotNone(hub_instance.inspector)

    def test_log_anomaly_invokes_logger_methods(self):
        source_val = f"src_{uuid.uuid4().hex}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = f"details_{uuid.uuid4().hex}"
        telemetry_val = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.hub.logger, "log") as mock_log:
            self.hub.log_anomaly(source=source_val, severity=severity_val, details=details_val, telemetry_snapshot=telemetry_val)
            mock_log.assert_called_once()
            passed_data = mock_log.call_args[0][0]
            self.assertEqual(passed_data["source"], source_val)
            self.assertEqual(passed_data["severity"], severity_val)
            self.assertEqual(passed_data["details"], details_val)
            self.assertEqual(passed_data["telemetry_snapshot"], telemetry_val)

    def test_log_anomaly_fallback_to_log_anomaly_method(self):
        source_val = f"src_{uuid.uuid4().hex}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH"])
        details_val = f"details_{uuid.uuid4().hex}"
        
        delattr(self.hub.logger, "log")
        self.hub.logger.log_anomaly = lambda data: None

        with patch.object(self.hub.logger, "log_anomaly") as mock_log_anomaly:
            self.hub.log_anomaly(source=source_val, severity=severity_val, details=details_val)
            mock_log_anomaly.assert_called_once()
            passed_data = mock_log_anomaly.call_args[0][0]
            self.assertEqual(passed_data["source"], source_val)

    def test_aggregate_and_report_returns_correct_dict(self):
        metric_name_val = f"metric_{uuid.uuid4().hex}"
        value_val = random.uniform(1.0, 100.0)

        with patch.object(self.hub.logger, "get_anomalies", return_value=[{uuid.uuid4().hex}]):
            res = self.hub.aggregate_and_report(metric_name=metric_name_val, value=value_val)
            self.assertIsInstance(res, dict)
            self.assertTrue(res["aggregated"])
            self.assertEqual(res["score"], value_val)
            self.assertEqual(res["metric_name"], metric_name_val)
            self.assertEqual(res["total_anomalies"], 1)

    def test_generate_final_report_returns_success_status(self):
        with patch.object(self.hub.logger, "get_anomalies", return_value=[]):
            res = self.hub.generate_final_report()
            self.assertIsInstance(res, dict)
            self.assertEqual(res["status"], "verified")
            self.assertEqual(res["code"], "success")
            self.assertEqual(res["anomalies_count"], 0)

    def test_start_new_with_stream_source(self):
        token_val = uuid.uuid4().hex
        repo_p = f"/path/{uuid.uuid4().hex}"
        dynamic_input = {
            "stream_source": True,
            "repo_path": repo_p,
            "token": token_val
        }
        mock_analysis_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("skills.patch_regression_hub.GitInspector") as mock_git_inspector_cls:
            mock_inspector_instance = mock_git_inspector_cls.return_value
            mock_inspector_instance.analyze_repository.return_value = mock_analysis_result
            
            res = start_new(dynamic_input)
            self.assertIsInstance(res, dict)
            self.assertEqual(res["token"], token_val)
            mock_git_inspector_cls.assert_called_once_with(repo_path=repo_p)
            mock_inspector_instance.analyze_repository.assert_called_once()

    def test_start_new_with_payload_id(self):
        payload_id_val = uuid.uuid4().hex
        target_val = f"target_{uuid.uuid4().hex}"
        error_rate_val = random.uniform(0.0, 1.0)
        severity_val = random.choice(["LOW", "HIGH"])
        
        dynamic_input = {
            "payload_id": payload_id_val,
            "target": target_val,
            "error_rate": error_rate_val,
            "severity_level": severity_val
        }

        with patch("skills.patch_regression_hub.AnomalyAuditHub") as mock_hub_cls:
            mock_hub_instance = mock_hub_cls.return_value
            mock_hub_instance.aggregate_and_report.return_value = {"aggregated": True, "score": error_rate_val}

            res = start_new(dynamic_input)
            mock_hub_cls.assert_called_once()
            mock_hub_instance.log_anomaly.assert_called_once_with(
                source=payload_id_val, severity=severity_val, details="Payload anomaly logged"
            )
            mock_hub_instance.aggregate_and_report.assert_called_once_with(
                metric_name=target_val, value=error_rate_val
            )
            self.assertTrue(res["aggregated"])

    def test_start_new_default_flow(self):
        key_val = uuid.uuid4().hex
        detail_val = f"detail_{uuid.uuid4().hex}"
        target_val = f"target_{uuid.uuid4().hex}"
        numeric_metric_val = random.uniform(10, 50)

        dynamic_input = {
            key_val: detail_val,
            "target": target_val,
            "numeric_metric": numeric_metric_val
        }

        with patch("skills.patch_regression_hub.AnomalyAuditHub") as mock_hub_cls:
            mock_hub_instance = mock_hub_cls.return_value
            mock_hub_instance.generate_final_report.return_value = {"status": "verified"}

            res = start_new(dynamic_input)
            mock_hub_cls.assert_called_once()
            mock_hub_instance.log_anomaly.assert_any_call(source=key_val, severity="LOW", details=detail_val)
            mock_hub_instance.aggregate_and_report.assert_called_once_with(metric_name=target_val, value=numeric_metric_val)
            mock_hub_instance.generate_final_report.assert_called_once()
            self.assertEqual(res["status"], "verified")


if __name__ == "__main__":
    unittest.main()