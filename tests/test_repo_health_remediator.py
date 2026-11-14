import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.repo_health_remediator import RepoHealthRemediator

class TestRepoHealthRemediator(unittest.TestCase):

    def setUp(self):
        self.remediator = RepoHealthRemediator()
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_threshold = random.uniform(0.1, 99.9)
        self.random_action = ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_remediate_health_success(self):
        prediction_data = {
            "repo_id": self.random_repo_id,
            "metric": self.random_metric,
            "predicted_value": self.random_threshold + random.uniform(1.0, 10.0),
            "threshold": self.random_threshold,
            "recommended_action": self.random_action
        }

        with patch('skills.repo_health_remediator.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "applied",
                "action_id": self.random_repo_id,
                "executed_action": self.random_action
            }
            mock_post.return_value = mock_response

            result = self.remediator.apply_remediation(prediction_data)

            self.assertEqual(result["status"], "applied")
            self.assertEqual(result["action_id"], self.random_repo_id)
            self.assertEqual(result["executed_action"], self.random_action)
            mock_post.assert_called_once()

    def test_remediate_health_no_action_needed(self):
        prediction_data = {
            "repo_id": self.random_repo_id,
            "metric": self.random_metric,
            "predicted_value": self.random_threshold - random.uniform(1.0, 10.0),
            "threshold": self.random_threshold,
            "recommended_action": self.random_action
        }

        with patch('skills.repo_health_remediator.requests.post') as mock_post:
            result = self.remediator.apply_remediation(prediction_data)

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["repo_id"], self.random_repo_id)
            mock_post.assert_not_called()

    def test_remediate_health_stream_io_payload(self):
        random_bytes = uuid.uuid4().bytes + b''.join(random.choices(string.ascii_letters.encode(), k=20))
        stream = io.BytesIO(random_bytes)

        with patch('skills.repo_health_remediator.requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "upload_status": "success",
                "checksum": str(hash(random_bytes))
            }
            mock_put.return_value = mock_response

            result = self.remediator.upload_remediation_logs(self.random_repo_id, stream)

            self.assertEqual(result["upload_status"], "success")
            self.assertIn("checksum", result)
            mock_put.assert_called_once()

    def test_remediate_health_failure_handling(self):
        prediction_data = {
            "repo_id": self.random_repo_id,
            "metric": self.random_metric,
            "predicted_value": self.random_threshold + random.uniform(10.0, 50.0),
            "threshold": self.random_threshold,
            "recommended_action": self.random_action
        }

        with patch('skills.repo_health_remediator.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = uuid.uuid4().hex
            mock_post.return_value = mock_response

            with self.assertRaises(RuntimeError):
                self.remediator.apply_remediation(prediction_data)

            mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()