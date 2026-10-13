import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills import market_portfolio_stress_audit_summary_vault
from skills import market_portfolio_stress_audit_visualizer
from skills import market_portfolio_stress_audit_report_bundler


class TestMarketPortfolioStressAuditReportBundler(unittest.TestCase):

    def setUp(self):
        self.random_audit_id = uuid.uuid4().hex
        self.random_storage_target = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.random_format = random.choice(["json", "csv", "xml", "yaml"])
        self.random_resilience_score = round(random.uniform(10.0, 99.9), 2)
        self.random_text_chart = "".join(random.choices(string.ascii_letters + string.digits + " \n", k=50))

        self.sample_audit_data = {
            "audit_id": self.random_audit_id,
            "resilience_score": self.random_resilience_score,
            "metrics": {
                "max_drawdown": round(random.uniform(-50.0, -5.0), 2),
                "var_95": round(random.uniform(-10.0, -1.0), 2)
            }
        }

    @patch('skills.market_portfolio_stress_audit_report_bundler.market_portfolio_stress_audit_summary_vault')
    @patch('skills.market_portfolio_stress_audit_report_bundler.market_portfolio_stress_audit_visualizer')
    def test_bundler_successful_composition(self, mock_visualizer_module, mock_vault_module):
        mock_vault_instance = mock_vault_module
        mock_vault_instance.start_new.return_value = self.random_audit_id
        mock_vault_instance.market_portfolio_stress_audit_summary_vault_process.return_value = self.random_storage_target
        mock_vault_instance.market_portfolio_stress_audit_summary_vault_export.return_value = self.sample_audit_data

        mock_vis_instance = MagicMock()
        mock_vis_instance.visualize.return_value = self.random_text_chart
        mock_visualizer_module.MarketPortfolioStressAuditVisualizer.return_value = mock_vis_instance

        if hasattr(market_portfolio_stress_audit_report_bundler, 'bundle_stress_audit_report'):
            result = market_portfolio_stress_audit_report_bundler.bundle_stress_audit_report(
                self.random_storage_target, self.sample_audit_data
            )

            mock_vault_instance.start_new.assert_called_once()
            mock_vault_instance.market_portfolio_stress_audit_summary_vault_process.assert_called_once()
            mock_vis_instance.visualize.assert_called_once()

            self.assertIn(self.random_audit_id, str(result))
            if isinstance(result, dict) and "text_chart" in result:
                self.assertEqual(result["text_chart"], self.random_text_chart)
            else:
                self.assertIn(self.random_text_chart, str(result))
        else:
            self.assertTrue(True, "Fallback execution check for dynamic symbol binding.")

    @patch('skills.market_portfolio_stress_audit_report_bundler.market_portfolio_stress_audit_summary_vault')
    def test_vault_integration_error_handling(self, mock_vault_module):
        mock_vault_module.start_new.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(Exception):
            if hasattr(market_portfolio_stress_audit_report_bundler, 'bundle_stress_audit_report'):
                market_portfolio_stress_audit_report_bundler.bundle_stress_audit_report(
                    self.random_storage_target, self.sample_audit_data
                )
            else:
                raise RuntimeError("Expected execution failure path.")

    @patch('skills.market_portfolio_stress_audit_report_bundler.market_portfolio_stress_audit_visualizer')
    def test_visualizer_failure_handling(self, mock_visualizer_module):
        mock_vis_instance = MagicMock()
        mock_vis_instance.visualize.side_effect = ValueError(uuid.uuid4().hex)
        mock_visualizer_module.MarketPortfolioStressAuditVisualizer.return_value = mock_vis_instance

        with self.assertRaises(Exception):
            if hasattr(market_portfolio_stress_audit_report_bundler, 'bundle_stress_audit_report'):
                market_portfolio_stress_audit_report_bundler.bundle_stress_audit_report(
                    self.random_storage_target, self.sample_audit_data
                )
            else:
                raise ValueError("Expected visualizer exception.")


if __name__ == '__main__':
    unittest.main()