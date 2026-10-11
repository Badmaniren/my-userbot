import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_regulatory_compliance_validator import validate_regulatory_compliance
from skills.db_storage import save_audit_record, fetch_audit_record
from skills.market_portfolio_audit_compliance_hub import evaluate_compliance_status
from skills.market_portfolio_audit_log_exporter import export_audit_logs

class IntegrationTestMarketPortfolioRegulatoryComplianceValidator(unittest.TestCase):

    def test_regulatory_compliance_pipeline_integration(self):
        unique_portfolio_id = f"port-{uuid.uuid4()}"
        limit_threshold = round(random.uniform(50000.0, 500000.0), 2)
        stress_factor = round(random.uniform(0.05, 0.35), 4)

        portfolio_payload = {
            "portfolio_id": unique_portfolio_id,
            "total_value": limit_threshold * random.uniform(0.8, 1.2),
            "stress_drawdown": stress_factor,
            "assets": [
                {"ticker": "AAPL", "allocation": 0.5, "risk_score": random.uniform(1.0, 5.0)},
                {"ticker": "GOOGL", "allocation": 0.5, "risk_score": random.uniform(1.0, 5.0)}
            ]
        }

        validation_result = validate_regulatory_compliance(portfolio_payload)

        self.assertIn("status", validation_result)
        self.assertIn("violations", validation_result)

        compliance_hub_evaluation = evaluate_compliance_status(unique_portfolio_id, validation_result)
        self.assertEqual(compliance_hub_evaluation["portfolio_id"], unique_portfolio_id)

        db_save_status = save_audit_record(unique_portfolio_id, compliance_hub_evaluation)
        self.assertTrue(db_save_status)

        fetched_record = fetch_audit_record(unique_portfolio_id)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record["portfolio_id"], unique_portfolio_id)

        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, f"audit_{unique_portfolio_id}.json")
            exported_file = export_audit_logs(unique_portfolio_id, export_path)

            self.assertTrue(os.path.exists(exported_file))
            self.assertGreater(os.path.getsize(exported_file), 0)

if __name__ == "__main__":
    unittest.main()