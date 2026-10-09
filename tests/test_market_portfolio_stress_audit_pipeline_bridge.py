import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills import market_portfolio_stress_audit_summary_vault as vault
from skills import market_portfolio_stress_audit_visualizer as visualizer
from skills.market_portfolio_stress_audit_pipeline_bridge import (
    MarketPortfolioStressAuditPipelineBridge,
    run_stress_audit_pipeline,
    market_portfolio_stress_audit_pipeline_bridge,
)


class TestMarketPortfolioStressAuditPipelineBridge(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"storage_{uuid.uuid4().hex}"
        self.random_audit_id = f"audit_{uuid.uuid4().hex}"
        self.random_format = random.choice(["json", "csv", "xml", "yaml"])
        self.random_metrics = {uuid.uuid4().hex: random.randint(1, 1000)}

    def test_bridge_class_initialization(self):
        bridge = MarketPortfolioStressAuditPipelineBridge(storage_target=self.random_storage)
        self.assertEqual(bridge.storage_target, self.random_storage)

    def test_bridge_initialize_audit(self):
        bridge = MarketPortfolioStressAuditPipelineBridge(storage_target=self.random_storage)
        with patch("skills.market_portfolio_stress_audit_summary_vault.start_new") as mock_start:
            expected_res = f"init_{uuid.uuid4().hex}"
            mock_start.return_value = expected_res
            result = bridge.initialize_audit()
            self.assertEqual(result, expected_res)
            mock_start.assert_called_once()

    def test_bridge_visualize_audit(self):
        bridge = MarketPortfolioStressAuditPipelineBridge(storage_target=self.random_storage)
        payload = {uuid.uuid4().hex: random.randint(10, 500)}
        with patch("skills.market_portfolio_stress_audit_visualizer.MarketPortfolioStressAuditVisualizer.visualize") as mock_vis:
            expected_res = f"vis_{uuid.uuid4().hex}"
            mock_vis.return_value = expected_res
            result = bridge.visualize_audit(payload)
            self.assertEqual(result, expected_res)
            mock_vis.assert_called_once_with(payload)

    def test_run_stress_audit_pipeline_success(self):
        payload = {
            "storage_target": self.random_storage,
            "expected_audit_id": self.random_audit_id,
            "audit_data": self.random_metrics,
            "format": self.random_format
        }

        with patch("skills.market_portfolio_stress_audit_summary_vault.start_new") as mock_start, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process") as mock_process, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_export") as mock_export, \
             patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_vis:

            mock_start.return_value = f"generated_{uuid.uuid4().hex}"

            result = run_stress_audit_pipeline(payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("audit_id"), self.random_audit_id)
            self.assertEqual(result.get("status"), "success")

            mock_process.assert_called_once_with(self.random_storage, self.random_metrics)
            mock_validate.assert_called_once_with(self.random_storage, self.random_audit_id)
            mock_export.assert_called_once_with(self.random_storage, self.random_format)
            mock_vis.assert_called_once_with(payload)

    def test_run_stress_audit_pipeline_with_audit_stream(self):
        stream_data = {uuid.uuid4().hex: f"val_{uuid.uuid4().hex}"}
        payload = {
            "storage_target": self.random_storage,
            "audit_stream": stream_data,
            "format": self.random_format
        }

        with patch("skills.market_portfolio_stress_audit_summary_vault.start_new") as mock_start, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process") as mock_process, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_export") as mock_export, \
             patch("skills.market_portfolio_stress_audit_visualizer.market_portfolio_stress_audit_visualizer") as mock_vis:

            fallback_id = f"fallback_{uuid.uuid4().hex}"
            mock_start.return_value = fallback_id

            result = run_stress_audit_pipeline(payload)

            self.assertEqual(result.get("audit_id"), fallback_id)
            self.assertEqual(result.get("status"), "success")
            mock_process.assert_called_once_with(self.random_storage, stream_data)

    def test_market_portfolio_stress_audit_pipeline_bridge_execution(self):
        payload = {
            "storage_target": self.random_storage,
            "audit_id": self.random_audit_id,
            "metrics": self.random_metrics
        }

        with patch("skills.market_portfolio_stress_audit_summary_vault.start_new") as mock_start, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_process") as mock_process, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_validate") as mock_validate, \
             patch("skills.market_portfolio_stress_audit_summary_vault.market_portfolio_stress_audit_summary_vault_export") as mock_export, \
             patch("skills.market_portfolio_stress_audit_visualizer.MarketPortfolioStressAuditVisualizer.visualize") as mock_vis:

            result = market_portfolio_stress_audit_pipeline_bridge(payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("audit_id"), self.random_audit_id)
            self.assertEqual(result.get("result"), "completed")

            mock_start.assert_called_once()
            mock_process.assert_called_once_with(self.random_storage, self.random_metrics)
            mock_validate.assert_called_once_with(self.random_storage, self.random_audit_id)
            mock_export.assert_called_once_with(self.random_storage, "json")
            mock_vis.assert_called_once_with(payload)


if __name__ == "__main__":
    unittest.main()