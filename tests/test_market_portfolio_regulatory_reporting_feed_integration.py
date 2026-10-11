import unittest
import uuid
import random
import os

from skills.market_portfolio_regulatory_reporting_feed import market_portfolio_regulatory_reporting_feed
from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
from skills.market_portfolio_stress_audit_exporter_v2 import market_portfolio_stress_audit_exporter_v2
from skills.db_storage import db_storage

class TestMarketPortfolioRegulatoryReportingFeedIntegration(unittest.TestCase):
    def test_regulatory_reporting_feed_integration(self):
        unique_run_id = str(uuid.uuid4())
        portfolio_id = f"port_{random.randint(10000, 99999)}"
        stress_score = round(random.uniform(1.0, 100.0), 4)

        audit_data = {
            "run_id": unique_run_id,
            "portfolio_id": portfolio_id,
            "stress_score": stress_score,
            "metrics": {
                "var_95": random.uniform(1000.0, 50000.0),
                "expected_shortfall": random.uniform(500.0, 25000.0)
            }
        }

        vault_res = market_portfolio_stress_audit_summary_vault(audit_data)
        self.assertIsNotNone(vault_res)

        export_config = {
            "run_id": unique_run_id,
            "format": "v2",
            "destination": f"./test_export_{unique_run_id}.json"
        }
        exporter_res = market_portfolio_stress_audit_exporter_v2(export_config)
        self.assertTrue(os.path.exists(export_config["destination"]))

        feed_payload = {
            "run_id": unique_run_id,
            "portfolio_id": portfolio_id,
            "report_type": "REGULATORY_COMPLIANCE_FEED"
        }
        feed_result = market_portfolio_regulatory_reporting_feed(feed_payload)

        self.assertIsInstance(feed_result, dict)
        self.assertEqual(feed_result.get("status"), "SUCCESS")
        self.assertEqual(feed_result.get("run_id"), unique_run_id)

        db_record = db_storage(f"SELECT * FROM regulatory_feeds WHERE run_id = '{unique_run_id}'")
        self.assertIsNotNone(db_record)

        if os.path.exists(export_config["destination"]):
            os.remove(export_config["destination"])

if __name__ == "__main__":
    unittest.main()