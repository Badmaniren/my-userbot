import unittest
import os
import uuid
from skills import market_portfolio_stress_audit_summary_vault
from skills import market_portfolio_stress_alert_trigger

class TestMarketPortfolioStressAlertTriggerIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_stress_vault_{uuid.uuid4()}.db"
        self.expected_audit_id = str(uuid.uuid4())
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = "http://localhost:8000/webhook"
        self.telegram_token = "mock_telegram_token_12345"
        self.chat_id = "-100123456789"
        self.severity_level = "HIGH"
        self.min_threshold = 0.15
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_stress_threshold_breach_flow(self):
        audit_payload = {
            "audit_id": self.expected_audit_id,
            "status": "BREACH",
            "max_drawdown": 0.25,
            "var_stress": 0.30
        }

        market_portfolio_stress_audit_summary_vault.start_new(self.storage_file)
        market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process(
            self.storage_file, audit_payload
        )

        result = market_portfolio_stress_alert_trigger.run(
            storage_file=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(result, "Integration trigger should return True when stress thresholds are breached.")

    def test_integration_stress_threshold_normal_flow(self):
        audit_payload = {
            "audit_id": self.expected_audit_id,
            "status": "NORMAL",
            "max_drawdown": 0.05,
            "var_stress": 0.08
        }

        market_portfolio_stress_audit_summary_vault.start_new(self.storage_file)
        market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process(
            self.storage_file, audit_payload
        )

        result = market_portfolio_stress_alert_trigger.run(
            storage_file=self.storage_file,
            expected_audit_id=self.expected_audit_id,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertFalse(result, "Integration trigger should return False when stress metrics are within acceptable limits.")

if __name__ == "__main__":
    unittest.main()