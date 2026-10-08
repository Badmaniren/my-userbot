import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.market_portfolio_stress_audit_webhook_publisher import (
    MarketPortfolioStressAuditWebhookPublisher,
    market_portfolio_stress_audit_webhook_publisher
)

class TestMarketPortfolioStressAuditWebhookPublisher(unittest.TestCase):

    def setUp(self):
        self.webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.auth_token = uuid.uuid4().hex
        self.audit_id = uuid.uuid4().hex
        self.error_tracking_id = uuid.uuid4().hex
        self.publisher = MarketPortfolioStressAuditWebhookPublisher(
            webhook_url=self.webhook_url,
            auth_token=self.auth_token
        )

    def test_get_headers_with_auth(self):
        headers = self.publisher._get_headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], f"Bearer {self.auth_token}")

    def test_get_headers_without_auth(self):
        pub_no_auth = MarketPortfolioStressAuditWebhookPublisher(webhook_url=self.webhook_url)
        headers = pub_no_auth._get_headers()
        self.assertEqual(headers, {})

    def test_publish_success(self):
        payload = {
            "audit_id": self.audit_id,
            "metric": random.uniform(1.0, 100.0)
        }
        expected_response = {"status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_webhook_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            result = self.publisher.publish(payload)

            mock_post.assert_called_once_with(
                self.webhook_url,
                json=payload,
                headers=self.publisher._get_headers()
            )
            self.assertEqual(result, expected_response)

    def test_publish_failure(self):
        payload = {
            "audit_id": self.audit_id,
            "error_tracking_id": self.error_tracking_id
        }

        with patch("skills.market_portfolio_stress_audit_webhook_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_post.return_value = mock_resp

            with self.assertRaises(ValueError) as ctx:
                self.publisher.publish(payload)

            self.assertIn(self.error_tracking_id, str(ctx.exception))

    def test_publish_stream_success(self):
        report_meta = {"meta_id": uuid.uuid4().hex}
        file_content = uuid.uuid4().hex.encode('utf-8')
        file_stream = io.BytesIO(file_content)
        expected_response = {"stream_status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_audit_webhook_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            result = self.publisher.publish_stream(report_meta, file_stream)

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            self.assertEqual(call_kwargs["data"], report_meta)
            self.assertIn("file", call_kwargs["files"])
            self.assertEqual(result, expected_response)

    def test_publish_stream_failure(self):
        report_meta = {"meta_id": uuid.uuid4().hex}
        file_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        err_code = random.choice([400, 401, 403, 404, 500, 502, 503])

        with patch("skills.market_portfolio_stress_audit_webhook_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = err_code
            mock_post.return_value = mock_resp

            with self.assertRaises(ValueError) as ctx:
                self.publisher.publish_stream(report_meta, file_stream)

            self.assertIn(str(err_code), str(ctx.exception))

    def test_functional_helper_flow(self):
        stored_data = {
            "audit_id": self.audit_id,
            "val": random.randint(100, 999)
        }
        api_response = {"delivered": True, "token": uuid.uuid4().hex}

        mock_db_storage = MagicMock()
        mock_db_storage.get_audit_record.side_effect = [
            {"data": stored_data},
            {"data": stored_data, "webhook_dispatched": False}
        ]

        with patch.dict(sys.modules, {"skills.db_storage": MagicMock(db_storage=mock_db_storage)}):
            with patch("skills.market_portfolio_stress_audit_webhook_publisher.requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = api_response
                mock_post.return_value = mock_resp

                res = market_portfolio_stress_audit_webhook_publisher(self.audit_id, self.webhook_url)

                self.assertEqual(res["status"], "success")
                self.assertEqual(res["audit_id"], self.audit_id)
                self.assertEqual(res["delivery_status"], "SUCCESS")
                self.assertEqual(res["response"], api_response)

                mock_db_storage.save_audit_record.assert_called_once()
                saved_record = mock_db_storage.save_audit_record.call_args[0][0]
                self.assertTrue(saved_record.get("webhook_dispatched"))

if __name__ == '__main__':
    unittest.main()