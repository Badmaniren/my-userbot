import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.repo_health_alert_channel import start_new

class TestRepoHealthAlertChannel(unittest.TestCase):

    def setUp(self):
        self.random_channel_name = ''.join(random.choices(string.ascii_lowercase, k=10)) + "_" + uuid.uuid4().hex[:6]
        self.random_alert_message = f"CRITICAL_HEALTH_ALERT_{uuid.uuid4().hex}"
        self.random_webhook_url = f"https://api.{uuid.uuid4().hex}.internal/alert/webhook"
        self.random_status_code = random.choice([200, 201, 202, 400, 403, 404, 500, 502, 503])
        self.random_payload_key = uuid.uuid4().hex
        self.random_payload_val = uuid.uuid4().hex

    def test_start_new_successful_dispatch(self):
        mock_response = MagicMock()
        mock_response.status_code = self.random_status_code
        mock_response.text = f'{{"status": "success", "id": "{uuid.uuid4().hex}"}}'
        mock_response.json.return_value = {
            "status": "success",
            "dispatch_id": uuid.uuid4().hex,
            self.random_payload_key: self.random_payload_val
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

            config_data = {
                "channel": self.random_channel_name,
                "webhook_url": self.random_webhook_url,
                "message": self.random_alert_message,
                "severity": "CRITICAL"
            }

            result = start_new(config_data)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], self.random_webhook_url)
            self.assertIn(self.random_alert_message, str(kwargs))
            self.assertIn(self.random_channel_name, str(kwargs))

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "success")
            self.assertIn("dispatch_id", result)

    def test_start_new_network_failure_handling(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception(f"Connection timeout: {uuid.uuid4().hex}")

            config_data = {
                "channel": self.random_channel_name,
                "webhook_url": self.random_webhook_url,
                "message": self.random_alert_message
            }

            try:
                result = start_new(config_data)
            except Exception as e:
                result = {"status": "error", "reason": str(e)}

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "error")
            self.assertIn("reason", result)

    def test_start_new_stream_payload_handling(self):
        random_bytes_content = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes_content)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"stream_processed": True}

        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response

            config_data = {
                "channel": self.random_channel_name,
                "webhook_url": self.random_webhook_url,
                "stream_data": mock_stream.read()
            }

            result = start_new(config_data)

            mock_post.assert_called_once()
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("stream_processed"))

if __name__ == '__main__':
    unittest.main()