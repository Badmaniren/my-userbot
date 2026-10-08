import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import requests
import io

from skills.market_portfolio_stress_audit_webhook_dispatcher import (
    StressAuditWebhookDispatcher,
    WebhookPayloadValidationError,
    WebhookDispatchError,
    market_portfolio_stress_audit_webhook_dispatcher
)


class TestStressAuditWebhookDispatcher(unittest.TestCase):

    def setUp(self):
        self.webhook_url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.secret_token = uuid.uuid4().hex
        self.dispatcher = StressAuditWebhookDispatcher(self.webhook_url, self.secret_token)
        self.audit_id = uuid.uuid4().hex
        self.portfolio_id = uuid.uuid4().hex

    def test_validate_payload_success_var(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": random.choice(["SUCCESS", "FAILED", "PENDING"]),
            "var_value": round(random.uniform(100.0, 10000.0), 2)
        }
        try:
            self.dispatcher._validate_payload(payload)
        except Exception as e:
            self.fail(f"_validate_payload raised unexpected exception: {e}")

    def test_validate_payload_success_stress_loss(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": random.choice(["SUCCESS", "FAILED"]),
            "stress_loss_amount": round(random.uniform(500.0, 50000.0), 2)
        }
        try:
            self.dispatcher._validate_payload(payload)
        except Exception as e:
            self.fail(f"_validate_payload raised unexpected exception: {e}")

    def test_validate_payload_missing_required(self):
        for field in ["audit_id", "portfolio_id", "status"]:
            payload = {
                "audit_id": self.audit_id,
                "portfolio_id": self.portfolio_id,
                "status": "ACTIVE",
                "var_value": 123.45
            }
            del payload[field]
            with self.assertRaises(WebhookPayloadValidationError):
                self.dispatcher._validate_payload(payload)

    def test_validate_payload_missing_numeric_fields(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "ACTIVE"
        }
        with self.assertRaises(WebhookPayloadValidationError):
            self.dispatcher._validate_payload(payload)

    def test_validate_payload_invalid_type_numeric(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "ACTIVE",
            "var_value": uuid.uuid4().hex
        }
        with self.assertRaises(WebhookPayloadValidationError):
            self.dispatcher._validate_payload(payload)

    def test_generate_signature(self):
        test_data = uuid.uuid4().hex.encode('utf-8')
        sig1 = self.dispatcher._generate_signature(test_data)
        sig2 = self.dispatcher._generate_signature(test_data)
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)

    def test_dispatch_success(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "SUCCESS",
            "var_value": 1500.50
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = self.dispatcher.dispatch(payload)
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_kwargs = mock_post.call_args[1]
            self.assertIn("headers", called_kwargs)
            self.assertIn("X-Signature", called_kwargs["headers"])
            self.assertEqual(called_kwargs["json"], payload)

    def test_dispatch_network_error(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "SUCCESS",
            "var_value": 1500.50
        }

        with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Connection aborted")):
            with self.assertRaises(WebhookDispatchError):
                self.dispatcher.dispatch(payload)

    def test_dispatch_timeout_error(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "SUCCESS",
            "var_value": 1500.50
        }

        with patch('requests.post', side_effect=requests.exceptions.Timeout("Read timed out")):
            with self.assertRaises(WebhookDispatchError):
                self.dispatcher.dispatch(payload)

    def test_dispatch_http_error(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "SUCCESS",
            "var_value": 1500.50
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
            mock_post.return_value = mock_response

            with self.assertRaises(WebhookDispatchError):
                self.dispatcher.dispatch(payload)

    def test_dispatch_general_request_exception(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "SUCCESS",
            "var_value": 1500.50
        }

        with patch('requests.post', side_effect=requests.exceptions.RequestException("Generic error")):
            with self.assertRaises(WebhookDispatchError):
                self.dispatcher.dispatch(payload)

    def test_market_portfolio_stress_audit_webhook_dispatcher_wrapper(self):
        payload = {
            "audit_id": self.audit_id,
            "portfolio_id": self.portfolio_id,
            "status": "ALERT",
            "stress_loss_amount": -7500.25
        }

        with patch('skills.market_portfolio_stress_audit_webhook_dispatcher.StressAuditWebhookDispatcher.dispatch') as mock_dispatch, \
             patch('skills.db_storage.db_storage') as mock_db:

            mock_dispatch.return_value = True
            mock_db.return_value = {"status": "UPDATED"}

            res = market_portfolio_stress_audit_webhook_dispatcher(
                audit_id=self.audit_id,
                webhook_url=self.webhook_url,
                payload=payload
            )

            self.assertEqual(res["dispatch_id"], self.audit_id)
            self.assertEqual(res["status"], "SUCCESS")
            self.assertEqual(res["audit_id"], self.audit_id)
            mock_dispatch.assert_called_once()
            mock_db.assert_called_once()


if __name__ == '__main__':
    unittest.main()