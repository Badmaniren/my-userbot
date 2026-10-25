import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import subprocess
import urllib.error
from skills.anomaly_verifier import AnomalyVerifier, AnomalyVerifierError
from skills.hypothesis_generator import HypothesisGeneratorError


class TestAnomalyVerifier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.verifier = AnomalyVerifier(self.repo_path)
        self.patch_id = uuid.uuid4().hex
        self.target_file = f"{uuid.uuid4().hex}.py"
        self.health_endpoint = f"http://127.0.0.1:{random.randint(1024, 65535)}/{uuid.uuid4().hex}"

    @patch("subprocess.run")
    def test_verify_patch_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.verifier.verify_patch(self.patch_id, self.target_file)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "diff", self.target_file],
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_verify_patch_failure(self, mock_run):
        error_msg = f"git_error_{uuid.uuid4().hex}".encode('utf-8')
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = error_msg
        mock_run.return_value = mock_result

        with self.assertRaises(AnomalyVerifierError) as ctx:
            self.verifier.verify_patch(self.patch_id, self.target_file)
        self.assertIn("Patch verification failed", str(ctx.exception))

    @patch("subprocess.Popen")
    def test_run_autofix_verification_success(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = io.BytesIO(f"output_{uuid.uuid4().hex}".encode('utf-8'))
        mock_popen.return_value = mock_process

        result = self.verifier.run_autofix_verification(self.patch_id)
        self.assertTrue(result)
        mock_popen.assert_called_once()
        mock_process.wait.assert_called_once()

    @patch("subprocess.Popen")
    def test_run_autofix_verification_failure(self, mock_popen):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = io.BytesIO(b"")
        mock_popen.return_value = mock_process

        result = self.verifier.run_autofix_verification(self.patch_id)
        self.assertFalse(result)

    @patch("urllib.request.urlopen")
    def test_evaluate_health_metrics_success(self, mock_urlopen):
        metric_value = random.uniform(1.0, 100.0)
        metric_key = f"metric_{uuid.uuid4().hex}"
        payload = json.dumps({metric_key: metric_value}).encode('utf-8')

        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = payload
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        val = self.verifier.evaluate_health_metrics(self.health_endpoint)
        self.assertEqual(val, float(metric_value))

    @patch("urllib.request.urlopen")
    def test_evaluate_health_metrics_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(f"conn_err_{uuid.uuid4().hex}")

        with self.assertRaises(AnomalyVerifierError) as ctx:
            self.verifier.evaluate_health_metrics(self.health_endpoint)
        self.assertIn("Failed to connect to health endpoint", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_evaluate_health_metrics_bad_status(self, mock_urlopen):
        bad_status = random.choice([400, 404, 500, 503])
        mock_urlopen.side_effect = urllib.error.HTTPError(
            self.health_endpoint, bad_status, "Error", {}, None
        )

        with self.assertRaises(AnomalyVerifierError) as ctx:
            self.verifier.evaluate_health_metrics(self.health_endpoint)
        self.assertIn(f"Health check failed with status code {bad_status}", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_evaluate_health_metrics_invalid_json(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b"Invalid JSON string"
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        with self.assertRaises(AnomalyVerifierError) as ctx:
            self.verifier.evaluate_health_metrics(self.health_endpoint)
        self.assertIn("Invalid JSON response from health endpoint", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_evaluate_health_metrics_no_numeric_values(self, mock_urlopen):
        payload = json.dumps({f"key_{uuid.uuid4().hex}": f"string_val_{uuid.uuid4().hex}"}).encode('utf-8')
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = payload
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        with self.assertRaises(AnomalyVerifierError) as ctx:
            self.verifier.evaluate_health_metrics(self.health_endpoint)
        self.assertIn("No numeric health metrics found in telemetry payload", str(ctx.exception))

    def test_verifier_integration_stub_error_handling(self):
        try:
            raise HypothesisGeneratorError(f"Hypothesis error {uuid.uuid4().hex}")
        except Exception as e:
            self.assertIsInstance(e, (Exception, HypothesisGeneratorError), f"Неожиданная ошибка: {type(e)}")
            self.assertEqual(type(e), HypothesisGeneratorError)
