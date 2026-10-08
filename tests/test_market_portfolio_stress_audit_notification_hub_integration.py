import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_notification_hub import market_portfolio_stress_audit_notification_hub
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_telegram_notifier import market_portfolio_telegram_notifier
from skills.market_portfolio_webhook_sync import market_portfolio_webhook_sync
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway

class TestMarketPortfolioStressAuditNotificationHubIntegration(unittest.TestCase):
    def test_notification_hub_routing_and_dispatch(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        random_stress_score = round(random.uniform(10.5, 95.8), 2)
        audit_reference_id = f"audit_{uuid.uuid4().hex[:10]}"
        
        vault_payload = {
            "portfolio_id": unique_portfolio_id,
            "audit_id": audit_reference_id,
            "stress_score": random_stress_score,
            "status": "CRITICAL_RISK"
        }
        
        vault_result = market_portfolio_stress_audit_summary_vault(vault_payload)
        self.assertIsNotNone(vault_result)

        hub_payload = {
            "audit_id": audit_reference_id,
            "portfolio_id": unique_portfolio_id,
            "channels": ["telegram", "webhook", "api"],
            "severity": "HIGH",
            "metrics": {
                "stress_score": random_stress_score
            }
        }

        dispatch_response = market_portfolio_stress_audit_notification_hub(hub_payload)
        
        self.assertIsInstance(dispatch_response, dict)
        self.assertIn("dispatch_status", dispatch_response)
        self.assertEqual(dispatch_response.get("audit_id"), audit_reference_id)
        
        tg_verification = market_portfolio_telegram_notifier({
            "audit_id": audit_reference_id,
            "target": unique_portfolio_id
        })
        self.assertIsNotNone(tg_verification)

        webhook_verification = market_portfolio_webhook_sync({
            "audit_id": audit_reference_id,
            "payload": hub_payload
        })
        self.assertIsNotNone(webhook_verification)

        api_verification = market_portfolio_api_gateway({
            "action": "get_notification_status",
            "audit_id": audit_reference_id
        })
        self.assertIsNotNone(api_verification)

if __name__ == "__main__":
    unittest.main()