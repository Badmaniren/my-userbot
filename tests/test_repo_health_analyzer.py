import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import requests
import io
from skills.repo_health_analyzer import RepoHealthAnalyzer


class TestRepoHealthAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoHealthAnalyzer()

    def test_fetch_and_analyze_success(self):
        random_repo_id = str(uuid.uuid4())
        random_key = "".join(random.choices(string.ascii_lowercase, k=8))
        random_val = random.randint(1, 100)
        mock_response_data = {
            "repo_id": random_repo_id,
            "metrics": {random_key: random_val}
        }
        random_url = f"https://{uuid.uuid4().hex}.org/api/v1/repo"

        with patch("skills.repo_health_analyzer.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            result = self.analyzer.fetch_and_analyze(random_url)

            mock_get.assert_called_once_with(random_url)
            self.assertEqual(result["repo_id"], random_repo_id)
            self.assertEqual(result["metrics"][random_key], random_val)
            self.assertFalse(result["anomaly_detected"])

    def test_fetch_and_analyze_request_exception(self):
        random_url = f"https://{uuid.uuid4().hex}.net/fail"

        with patch("skills.repo_health_analyzer.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection aborted")

            with self.assertRaises(requests.exceptions.RequestException):
                self.analyzer.fetch_and_analyze(random_url)

    def test_evaluate_anomalies_critical_alert_true(self):
        tag_id = f"metric-{uuid.uuid4().hex[:6]}"
        threshold = float(random.randint(10, 50))
        complexity = float(random.randint(1, 9))
        detected_num = threshold + float(random.randint(1, 20))

        codebase_metrics = {
            "tag": tag_id,
            "complexity_index": complexity,
            "threshold": threshold
        }
        html_dump = f"<html><body><div id='{tag_id}'>{detected_num}</div></body></html>"

        result = self.analyzer.evaluate_anomalies(codebase_metrics, html_dump)

        self.assertEqual(result["target_tag"], tag_id)
        self.assertTrue(result["critical_alert"])
        self.assertEqual(result["detected_value"], detected_num)

    def test_evaluate_anomalies_critical_alert_false_fallback_complexity(self):
        tag_id = f"metric-{uuid.uuid4().hex[:6]}"
        threshold = float(random.randint(50, 100))
        complexity = float(random.randint(1, 40))

        codebase_metrics = {
            "tag": tag_id,
            "complexity_index": complexity,
            "threshold": threshold
        }
        html_dump = f"<html><body><div id='nonexistent'>some text</div></body></html>"

        result = self.analyzer.evaluate_anomalies(codebase_metrics, html_dump)

        self.assertEqual(result["target_tag"], tag_id)
        self.assertFalse(result["critical_alert"])
        self.assertEqual(result["detected_value"], complexity)

    def test_process_health_stream_success(self):
        random_endpoint = f"https://{uuid.uuid4().hex}.io/stream"
        mock_stream = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.repo_health_analyzer.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            try:
                self.analyzer.process_health_stream(random_endpoint, mock_stream)
            except Exception as e:
                self.fail(f"process_health_stream raised unexpected exception: {e}")

            mock_get.assert_called_once_with(random_endpoint)

    def test_process_health_stream_raises_runtime_error(self):
        random_endpoint = f"https://{uuid.uuid4().hex}.io/stream-error"
        mock_stream = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.repo_health_analyzer.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Timeout")

            with self.assertRaises(RuntimeError):
                self.analyzer.process_health_stream(random_endpoint, mock_stream)

    def test_generate_optimization_patch_optimal(self):
        module_name = f"mod_{uuid.uuid4().hex[:8]}"
        patch_id = str(uuid.uuid4())
        score = random.randint(50, 100)

        input_data = {
            "module": module_name,
            "patch_uuid": patch_id,
            "score": score
        }

        result = self.analyzer.generate_optimization_patch(input_data)

        self.assertEqual(result["patch_uuid"], patch_id)
        self.assertEqual(result["target_module"], module_name)
        self.assertEqual(result["action_code"], "OPTIMAL")

    def test_generate_optimization_patch_refactor(self):
        module_name = f"mod_{uuid.uuid4().hex[:8]}"
        patch_id = str(uuid.uuid4())
        score = random.randint(0, 49)

        input_data = {
            "module": module_name,
            "patch_uuid": patch_id,
            "score": score
        }

        result = self.analyzer.generate_optimization_patch(input_data)

        self.assertEqual(result["patch_uuid"], patch_id)
        self.assertEqual(result["target_module"], module_name)
        self.assertEqual(result["action_code"], "REFACTOR_REQUIRED")

    def test_analyze_health_with_anomalies(self):
        repo_path = f"/var/repo/{uuid.uuid4().hex}"
        threshold = 50.0
        metrics = {
            f"metric_{uuid.uuid4().hex[:4]}": 75.0,
            f"metric_{uuid.uuid4().hex[:4]}": 80.0,
            f"metric_{uuid.uuid4().hex[:4]}": 20.0
        }
        audit_dummy_result = {"status": "audited", "uuid": uuid.uuid4().hex}

        with patch("skills.repo_health_analyzer.RepoAuditor") as mock_auditor_cls:
            mock_auditor_instance = mock_auditor_cls.return_value
            mock_auditor_instance.audit_repository.return_value = audit_dummy_result

            result = self.analyzer.analyze_health(repo_path, threshold, metrics)

            mock_auditor_instance.audit_repository.assert_called_once_with(repo_path)
            self.assertEqual(result["health_score"], 80.0)
            self.assertEqual(len(result["anomalies_detected"]), 2)
            self.assertEqual(result["audit_details"], audit_dummy_result)


class TestRepoHealthAnalyzerIntegration(unittest.TestCase):

    def test_full_health_lifecycle(self):
        analyzer = RepoHealthAnalyzer()
        random_repo_path = f"/home/user/repos/{uuid.uuid4().hex}"
        random_threshold = float(random.randint(30, 60))
        metric_name = f"cpu_load_{uuid.uuid4().hex[:4]}"
        high_val = random_threshold + float(random.randint(10, 40))

        metrics = {metric_name: high_val}
        audit_mock_data = {"repo_path": random_repo_path, "issues_found": random.randint(1, 5)}

        with patch("skills.repo_health_analyzer.RepoAuditor") as mock_auditor:
            mock_auditor.return_value.audit_repository.return_value = audit_mock_data

            analysis_result = analyzer.analyze_health(random_repo_path, random_threshold, metrics)

            self.assertIn(metric_name, analysis_result["anomalies_detected"])
            self.assertEqual(analysis_result["audit_details"], audit_mock_data)

            patch_payload = {
                "module": metric_name,
                "patch_uuid": str(uuid.uuid4()),
                "score": int(analysis_result["health_score"])
            }
            opt_result = analyzer.generate_optimization_patch(patch_payload)
            self.assertEqual(opt_result["target_module"], metric_name)
            self.assertIn(opt_result["action_code"], ["OPTIMAL", "REFACTOR_REQUIRED"])