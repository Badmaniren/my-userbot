import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_audit_notification_hub import start_v2, market_portfolio_stress_audit_notification_hub

class TestMarketPortfolioStressAuditNotificationHub(unittest.TestCase):

    def test_start_new_telegram_success(self):
        target_channel = f"channel_{uuid.uuid4().hex[:8]}"
        payload = {
            "audit_id": uuid.uuid4().hex,
            "metric": random.randint(100, 999),
            "status": ''.join(random.choices(string.ascii_lowercase, k=6))
        }
        notifier_type = "telegram"
        expected_res = {"success": True, "chat": target_channel}

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_telegram_notifier") as mock_telegram, \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage") as mock_db:
            
            mock_telegram.send_notification.return_value = expected_res
            
            res = start_v2(target_channel, payload, notifier_type)
            
            mock_telegram.send_notification.assert_called_once_with(target_channel, payload)
            mock_db.save_audit_log.assert_called_once_with(payload)
            self.assertEqual(res, expected_res)

    def test_start_new_webhook_success(self):
        target_channel = f"https://webhook.site/{uuid.uuid4().hex}"
        payload = {
            "audit_id": uuid.uuid4().hex,
            "portfolio_value": random.uniform(1000.0, 50000.0)
        }
        notifier_type = "webhook"
        
        mock_resp = MagicMock()
        mock_resp.status_code = random.choice([200, 201, 204])
        mock_resp.text = f"response_{uuid.uuid4().hex[:6]}"

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_webhook_sync") as mock_webhook, \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage") as mock_db:
            
            mock_webhook.post.return_value = mock_resp
            
            res = start_v2(target_channel, payload, notifier_type)
            
            mock_webhook.post.assert_called_once_with(target_channel, json=payload)
            mock_db.save_audit_log.assert_called_once_with(payload)
            self.assertEqual(res["status_code"], mock_resp.status_code)
            self.assertEqual(res["response_text"], mock_resp.text)

    def test_start_new_api_gateway_success(self):
        target_channel = f"gateway_{uuid.uuid4().hex[:6]}"
        payload = {
            "audit_id": uuid.uuid4().hex,
            "risk_score": random.random()
        }
        notifier_type = "api_gateway"
        
        random_bytes = f"stream_content_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_api_gateway") as mock_gateway, \
             patch("skills.market_portfolio_stress_audit_notification_hub.db_storage") as mock_db:
            
            mock_gateway.stream_audit_payload.return_value = mock_stream
            
            res = start_v2(target_channel, payload, notifier_type)
            
            mock_gateway.stream_audit_payload.assert_called_once_with(target_channel, payload)
            mock_db.save_audit_log.assert_called_once_with(payload)
            self.assertTrue(res["stream_processed"])
            self.assertEqual(res["content"], random_bytes)

    def test_start_new_unknown_notifier_type(self):
        target_channel = f"chan_{uuid.uuid4().hex[:4]}"
        payload = {"audit_id": uuid.uuid4().hex}
        notifier_type = f"unknown_{uuid.uuid4().hex[:4]}"

        with self.assertRaises(ValueError) as ctx:
            start_v2(target_channel, payload, notifier_type)
        
        self.assertIn(notifier_type, str(ctx.exception))

    def test_market_portfolio_stress_audit_notification_hub_dispatch(self):
        audit_id = uuid.uuid4().hex
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        channels = ["telegram", "webhook", "api"]
        
        hub_payload = {
            "audit_id": audit_id,
            "portfolio_id": portfolio_id,
            "channels": channels,
            "extra_data": uuid.uuid4().hex
        }

        mock_telegram_func = MagicMock(return_value={"telegram_status": "sent"})
        mock_webhook_func = MagicMock(return_value={"webhook_status": "delivered"})
        mock_api_func = MagicMock(return_value={"api_status": "active"})

        with patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_telegram_notifier", mock_telegram_func), \
             patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_webhook_sync", mock_webhook_func), \
             patch("skills.market_portfolio_stress_audit_notification_hub.market_portfolio_api_gateway", mock_api_func):
            
            res = market_portfolio_stress_audit_notification_hub(hub_payload)
            
            self.assertEqual(res["dispatch_status"], "success")
            self.assertEqual(res["audit_id"], audit_id)
            self.assertIn("telegram", res["results"])
            self.assertIn("webhook", res["results"])
            self.assertIn("api", res["results"])
            
            mock_telegram_func.assert_called_once_with({
                "audit_id": audit_id,
                "target": portfolio_id
            })
            mock_webhook_func.assert_called_once_with({
                "audit_id": audit_id,
                "payload": hub_payload
            })
            mock_api_func.assert_called_once_with({
                "action": "get_notification_status",
                "audit_id": audit_id
            })

if __name__ == "__main__":
    unittest.main()