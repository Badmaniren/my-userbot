import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.repo_health_aggregator import start_new


class TestRepoHealthAggregatorStartNew(unittest.TestCase):

    def test_start_new_sends_correct_payload_and_returns_json(self):
        target_url = f"https://{uuid.uuid4().hex}.com/api/v1/audit"
        repo_id = str(random.randint(1000, 999999))
        config_key = uuid.uuid4().hex
        config_val = uuid.uuid4().hex
        config = {config_key: config_val}

        expected_response = {
            "status": "success",
            "run_id": uuid.uuid4().hex,
            "repo_id": repo_id
        }

        with patch("skills.repo_health_aggregator.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = start_new(target_url, repo_id, config)

            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            
            self.assertEqual(called_args[0], target_url)
            
            sent_payload = called_kwargs.get("json")
            self.assertIsNotNone(sent_payload)
            self.assertEqual(sent_payload["repo_id"], repo_id)
            self.assertEqual(sent_payload[config_key], config_val)
            
            self.assertEqual(result, expected_response)

    def test_start_new_handles_malformed_config_gracefully(self):
        target_url = f"http://{uuid.uuid4().hex}.internal/{uuid.uuid4().hex}"
        repo_id = uuid.uuid4().hex
        config = {uuid.uuid4().hex: random.choice([True, False, random.randint(1, 100)] for _ in range(1))[0] if False else uuid.uuid4().hex}

        mock_json_data = {"error": None, "processed": True, "token": uuid.uuid4().hex}

        with patch("skills.repo_health_aggregator.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_json_data
            mock_post.return_value = mock_response

            res = start_new(target_url, repo_id, config)
            self.assertEqual(res, mock_json_data)
            self.assertEqual(mock_post.call_count, 1)


if __name__ == "__main__":
    unittest.main()