import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.repo_health_aggregator import start_new


class TestRepoHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_metric_value = random.uniform(0.0, 100.0)
        self.random_url = f"https://{uuid.uuid4().hex}.repo.internal/api/v1/health"
        self.random_payload = {
            "session_token": uuid.uuid4().hex,
            "audit_level": random.choice(["strict", "moderate", "lenient"]),
            "timeout": random.randint(10, 300)
        }

    def test_start_new_success_aggregation(self):
        random_bytes_content = f"HEALTH_OK_{uuid.uuid4().hex}".encode('utf-8')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "repo_id": self.random_repo_id,
            "score": self.random_metric_value,
            "metric": self.random_metric_name
        }
        mock_response.raw = io.BytesIO(random_bytes_content)

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(
                target_url=self.random_url,
                repo_id=self.random_repo_id,
                config=self.random_payload
            )

            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertIn(self.random_url, called_args)
            self.assertEqual(called_kwargs['json']['repo_id'], self.random_repo_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("repo_id"), self.random_repo_id)
            self.assertEqual(result.get("score"), self.random_metric_value)
            self.assertEqual(result.get("metric"), self.random_metric_name)

    def test_start_new_handles_network_anomaly(self):
        with patch('requests.post', side_effect=Exception(uuid.uuid4().hex)) as mock_post:
            with self.assertRaises(Exception):
                start_new(
                    target_url=self.random_url,
                    repo_id=self.random_repo_id,
                    config=self.random_payload
                )
            mock_post.assert_called_once()

    def test_start_new_empty_payload_fallback(self):
        random_error_code = random.choice([400, 401, 403, 404, 500, 503])
        mock_response = MagicMock()
        mock_response.status_code = random_error_code
        mock_response.json.return_value = {
            "error": uuid.uuid4().hex,
            "code": random_error_code
        }

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(
                target_url=self.random_url,
                repo_id=self.random_repo_id,
                config={}
            )

            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertEqual(result.get("code"), random_error_code)


if __name__ == '__main__':
    unittest.main()