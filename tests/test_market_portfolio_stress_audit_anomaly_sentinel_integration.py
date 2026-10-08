import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_anomaly_sentinel import (
    market_portfolio_stress_audit_anomaly_sentinel
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault
)
from skills.market_portfolio_alert_dispatcher import (
    market_portfolio_alert_dispatcher
)

class TestMarketPortfolioStressAuditAnomalySentinelIntegration(unittest.TestCase):
    def test_anomaly_sentinel_pipeline_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        stress_audit_id = f"audit_{uuid.uuid4().hex[:12]}"
        risk_spike_threshold = round(random.uniform(0.05, 0.45), 4)
        simulated_var_loss = round(random.uniform(10000.0, 500000.0), 2)

        audit_payload = {
            "portfolio_id": portfolio_id,
            "stress_audit_id": stress_audit_id,
            "threshold": risk_spike_threshold,
            "var_loss": simulated_var_loss,
            "anomaly_flags": ["sudden_liquidity_drain", "volatility_spike"]
        }

        vault_save_result = market_portfolio_stress_audit_summary_vault(audit_payload)
        self.assertIsNotNone(vault_save_result)

        sentinel_result = market_portfolio_stress_audit_anomaly_sentinel({
            "portfolio_id": portfolio_id,
            "stress_audit_id": stress_audit_id,
            "audit_data": audit_payload
        })

        self.assertIsInstance(sentinel_result, dict)
        self.assertIn("anomaly_detected", sentinel_result)
        self.assertIn("sentinel_event_id", sentinel_result)

        event_id = sentinel_result["sentinel_event_id"]
        self.assertTrue(isinstance(event_id, str))
        self.assertGreater(len(event_id), 0)

        dispatch_res = market_portfolio_alert_dispatcher({
            "event_id": event_id,
            "portfolio_id": portfolio_id,
            "anomaly_detected": sentinel_result["anomaly_detected"]
        })
        self.assertIsNotNone(dispatch_res)

        stored_record = db_storage({
            "action": "get",
            "key": event_id
        })
        self.assertIsNotNone(stored_record)

if __name__ == "__main__":
    unittest.main()