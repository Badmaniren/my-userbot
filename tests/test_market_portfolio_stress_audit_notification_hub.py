import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_audit_notification_hub import start_new


class TestMarketPortfolioStressAuditNotificationHub(unittest.TestCase):

    def setUp(self):
        self.random_hex = uuid.uuid4().hex
        self.channel_name = "".join(random.choices(string.ascii_lowercase, k=10))
        self.endpoint_url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1/notify"
        self.audit_id = f"audit-{random.randint(1000, 9999)}"
        self.payload_data = {
            "id": self.audit_id,
            "status": random.choice(["SUCCESS", "FAILURE", "CRITICAL"]),
            "score": round(random.uniform(0.0, 100.0), 2),
            "message": f"Stress test report {uuid.uuid4().hex[:6]}"
        }

    def test_start_new_telegram_dispatch(self):
        mock_db = MagicMock()
        mock_telegram = MagicMock()
        mock_webhook = MagicMock()
        mock_api = MagicMock()

        mock_telegram.send_notification.return_value = {
            "status": "sent",
            "channel": self.channel_name,
            "ref": self.random_hex
        }

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_telegram_notifier", mock_telegram), \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage", mock_db):

            result = start_new(
                target_channel=self.channel_name,
                payload=self.payload_data,
                notifier_type="telegram"
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("ref"), self.random_hex)
            mock_telegram.send_notification.assert_called_once()
            mock_db.save_audit_log.assert_called()

    def test_start_new_webhook_dispatch(self):
        mock_db = MagicMock()
        mock_webhook_client = MagicMock()
        
        expected_response_code = random.choice([200, 201, 202])
        mock_webhook_client.post.return_value.status_code = expected_response_code
        mock_webhook_client.post.return_value.text = f"ACK-{self.random_hex}"

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_webhook_sync", mock_webhook_client), \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage", mock_db):

            result = start_new(
                target_channel=self.endpoint_url,
                payload=self.payload_data,
                notifier_type="webhook"
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.get("status_code"), expected_response_code)
            self.assertIn(self.random_hex, result.get("response_text"))

    def test_start_new_stream_io_handling(self):
        mock_db = MagicMock()
        mock_gateway = MagicMock()
        
        random_stream_content = f"DATA-STREAM-{uuid.uuid4().hex}".encode('utf-8')
        fake_stream = io.BytesIO(random_stream_content)

        mock_gateway.stream_audit_payload.return_value = fake_stream

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_api_gateway", mock_gateway), \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage", mock_db):

            result = start_new(
                target_channel=self.endpoint_url,
                payload=self.payload_data,
                notifier_type="api_gateway"
            )

            self.assertTrue(result.get("stream_processed"))
            mock_gateway.stream_audit_payload.assert_called_once()

    def test_start_new_invalid_notifier_exception(self):
        invalid_notifier = f"unknown-channel-{uuid.uuid4().hex[:6]}"
        mock_db = MagicMock()

        with patch("skills.market_portfolio_stress_audit_notification_hub.db_storage", mock_db):
            with self.assertRaises(ValueError) as ctx:
                start_new(
                    target_channel=self.endpoint_url,
                    payload=self.payload_data,
                    notifier_type=invalid_notifier
                )
            
            self.assertIn(invalid_notifier, str(ctx.exception))