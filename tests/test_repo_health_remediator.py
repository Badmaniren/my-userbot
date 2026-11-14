import unittest
from unittest.mock import patch, MagicMock
import os
import json
import io
import uuid
import random
import string
from skills.repo_health_remediator import RepoHealthRemediator

class TestRepoHealthRemediator(unittest.TestCase):
    
    def setUp(self):
        self.api_endpoint = f"https://api.{uuid.uuid4().hex[:8]}.internal/{uuid.uuid4().hex[:6]}"
        self.remediator = RepoHealthRemediator(api_endpoint=self.api_endpoint)

    def test_apply_remediation_unit_skipped(self):
        repo_id = uuid.uuid4().hex
        metric = uuid.uuid4().hex
        predicted_value = random.uniform(0.1, 0.4)
        threshold = random.uniform(0.5, 0.9)
        recommended_action = uuid.uuid4().hex

        prediction_data = {
            "repo_id": repo_id,
            "metric": metric,
            "predicted_value": predicted_value,
            "threshold": threshold,
            "recommended_action": recommended_action
        }

        result = self.remediator.apply_remediation(prediction_data)
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["repo_id"], repo_id)

    @patch("skills.repo_health_remediator.requests.post")
    def test_apply_remediation_unit_success(self, mock_post):
        repo_id = uuid.uuid4().hex
        metric = uuid.uuid4().hex
        predicted_value = random.uniform(0.6, 1.0)
        threshold = random.uniform(0.1, 0.5)
        recommended_action = uuid.uuid4().hex

        expected_response = {
            "status": "remediated",
            "repo_id": repo_id,
            "action": recommended_action
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        prediction_data = {
            "repo_id": repo_id,
            "metric": metric,
            "predicted_value": predicted_value,
            "threshold": threshold,
            "recommended_action": recommended_action
        }

        result = self.remediator.apply_remediation(prediction_data)
        self.assertEqual(result, expected_response)
        mock_post.assert_called_once()

    @patch("skills.repo_health_remediator.requests.post")
    def test_apply_remediation_unit_failure(self, mock_post):
        repo_id = uuid.uuid4().hex
        metric = uuid.uuid4().hex
        predicted_value = random.uniform(0.6, 1.0)
        threshold = random.uniform(0.1, 0.5)
        recommended_action = uuid.uuid4().hex

        mock_response = MagicMock()
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        mock_response.status_code = status_code
        mock_post.return_value = mock_response

        prediction_data = {
            "repo_id": repo_id,
            "metric": metric,
            "predicted_value": predicted_value,
            "threshold": threshold,
            "recommended_action": recommended_action
        }

        with self.assertRaises(RuntimeError) as ctx:
            self.remediator.apply_remediation(prediction_data)
        self.assertIn(str(status_code), str(ctx.exception))

    @patch("skills.repo_health_remediator.RepoLogger")
    def test_apply_remediation_integration_scenario(self, mock_repo_logger_cls):
        repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        target_output = f"{repo_path}/{uuid.uuid4().hex}.json"
        prediction_id = uuid.uuid4().hex
        metric = uuid.uuid4().hex
        predicted_value = random.uniform(0.6, 1.0)
        threshold = random.uniform(0.1, 0.5)
        recommended_action = uuid.uuid4().hex

        mock_logger_instance = MagicMock()
        mock_repo_logger_cls.return_value = mock_logger_instance

        prediction_data = {
            "target_output": target_output,
            "repo_path": repo_path,
            "prediction_id": prediction_id,
            "prediction_data": {
                "metric": metric,
                "predicted_value": predicted_value,
                "threshold": threshold,
                "recommended_action": recommended_action
            }
        }

        try:
            result = self.remediator.apply_remediation(prediction_data)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["repo_path"], repo_path)

            self.assertTrue(os.path.exists(target_output))
            with open(target_output, "r", encoding="utf-8") as f:
                content = json.load(f)
                self.assertEqual(content["repo_path"], repo_path)
                self.assertEqual(content["metric"], metric)
                self.assertEqual(content["recommended_action"], recommended_action)
                self.assertEqual(content["status"], "success")

            mock_repo_logger_cls.assert_called_once_with(repo_path=repo_path)
            mock_logger_instance.log.assert_called_once()
        finally:
            if os.path.exists(target_output):
                os.remove(target_output)
            if os.path.exists(repo_path):
                try:
                    os.rmdir(repo_path)
                except OSError:
                    pass

    @patch("skills.repo_health_remediator.requests.put")
    def test_remediate_health_stream_io_payload(self, mock_put):
        repo_id = uuid.uuid4().hex
        random_bytes = uuid.uuid4().bytes + "".join(random.choices(string.ascii_letters, k=20)).encode("utf-8")
        stream = io.BytesIO(random_bytes)

        expected_checksum = str(hash(random_bytes))
        expected_response = {
            "upload_status": "success",
            "checksum": expected_checksum
        }

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = expected_response
        mock_put.return_value = mock_response

        result = self.remediator.upload_remediation_logs(repo_id, stream)
        self.assertEqual(result, expected_response)
        mock_put.assert_called_once()