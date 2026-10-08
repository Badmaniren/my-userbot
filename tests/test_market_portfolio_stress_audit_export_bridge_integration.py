import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_export_bridge import (
    db_storage,
    market_report_generator,
    market_portfolio_stress_audit_summary_vault,
    market_portfolio_stress_audit_visualizer,
    market_portfolio_stress_reporter,
    market_portfolio_data_exporter
)

class TestMarketPortfolioStressAuditExportBridgeIntegration(unittest.TestCase):
    def test_stress_audit_export_bridge_workflow(self):
        portfolio_id = str(uuid.uuid4())
        audit_score = round(random.uniform(10.0, 99.9), 2)
        report_format = random.choice(["pdf", "json", "csv"])

        vault_data = {
            "portfolio_id": portfolio_id,
            "audit_score": audit_score,
            "status": "STRESSED",
            "metric_code": random.randint(1000, 9999)
        }

        vault_result = market_portfolio_stress_audit_summary_vault(vault_data)
        self.assertIsNotNone(vault_result)

        visualizer_payload = {
            "portfolio_id": portfolio_id,
            "audit_score": audit_score,
            "render_mode": "vector"
        }
        chart_artifact = market_portfolio_stress_audit_visualizer(visualizer_payload)
        self.assertIsNotNone(chart_artifact)

        stress_report = market_portfolio_stress_reporter({
            "portfolio_id": portfolio_id,
            "score": audit_score
        })
        self.assertIsNotNone(stress_report)

        report_gen_request = {
            "portfolio_id": portfolio_id,
            "format": report_format,
            "content": stress_report
        }
        generated_report = market_report_generator(report_gen_request)
        self.assertIn(portfolio_id, str(generated_report))

        export_config = {
            "portfolio_id": portfolio_id,
            "destination": "local_storage",
            "payload": generated_report
        }
        export_result = market_portfolio_data_exporter(export_config)
        self.assertTrue(export_result)

        persisted_record = db_storage({
            "action": "get",
            "portfolio_id": portfolio_id
        })

        self.assertIsNotNone(persisted_record)
        self.assertEqual(persisted_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(persisted_record.get("audit_score"), audit_score)

if __name__ == "__main__":
    unittest.main()