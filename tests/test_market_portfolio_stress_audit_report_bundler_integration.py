import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_stress_audit_summary_vault import (
    start_new,
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate
)
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)
from skills.market_portfolio_stress_audit_report_bundler import (
    market_portfolio_stress_audit_report_bundler,
    MarketPortfolioStressAuditReportBundler
)

class TestMarketPortfolioStressAuditReportBundlerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.audit_id = f"audit-{uuid.uuid4()}"
        self.storage_filename = f"stress_audit_{uuid.uuid4()}.json"
        self.storage_target = os.path.join(self.test_dir.name, self.storage_filename)

        self.resilience_score = round(random.uniform(10.0, 99.9), 2)
        self.max_drawdown = round(random.uniform(-50.0, -1.0), 2)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)

        self.audit_payload = {
            "audit_id": self.audit_id,
            "resilience_score": self.resilience_score,
            "max_drawdown": self.max_drawdown,
            "portfolio_value": self.portfolio_value,
            "metrics": {
                "var_95": round(random.uniform(1000.0, 50000.0), 2),
                "cvar_95": round(random.uniform(2000.0, 70000.0), 2)
            }
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_bundler_workflow(self):
        mock_db = unittest.mock.MagicMock()
        init_res = start_new(db_storage=mock_db)
        self.assertIsNotNone(init_res)

        market_portfolio_stress_audit_summary_vault_process(
            storage_target=self.storage_target,
            audit_data=self.audit_payload
        )
        self.assertTrue(os.path.exists(self.storage_target))

        is_valid = market_portfolio_stress_audit_summary_vault_validate(
            file_path=self.storage_target,
            expected_audit_id=self.audit_id
        )
        self.assertTrue(is_valid)

        visualizer = MarketPortfolioStressAuditVisualizer()
        viz_result = visualizer.visualize(self.audit_payload)
        self.assertIsNotNone(viz_result)

        func_viz_result = market_portfolio_stress_audit_visualizer(self.audit_payload)
        self.assertIsNotNone(func_viz_result)

        bundle_payload = {
            "storage_path": self.storage_target,
            "audit_id": self.audit_id,
            "data": self.audit_payload
        }

        bundler_instance = MarketPortfolioStressAuditReportBundler()
        if hasattr(bundler_instance, "bundle"):
            bundle_result = bundler_instance.bundle(bundle_payload)
            self.assertIsNotNone(bundle_result)

        functional_bundle_result = market_portfolio_stress_audit_report_bundler(bundle_payload)
        self.assertIsNotNone(functional_bundle_result)

        if isinstance(functional_bundle_result, dict):
            self.assertIn("audit_id", functional_bundle_result)
            self.assertEqual(functional_bundle_result["audit_id"], self.audit_id)

if __name__ == "__main__":
    unittest.main()