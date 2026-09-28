import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_risk_analytics_hub import start_new, MarketPortfolioRiskAnalyticsHub

class TestMarketPortfolioRiskAnalyticsHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.volatility_limit = round(random.uniform(0.01, 0.5), 4)
        self.scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"
        self.projected_loss = round(random.uniform(100.0, 50000.0), 2)

    def test_start_new_integration_flow(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {
            "portfolio_id": self.portfolio_id,
            "volatility_limit": self.volatility_limit
        }

        mock_collector = MagicMock()
        mock_collector.stream_metrics.return_value = True

        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_collector_agent": mock_collector
        }

        result = start_new(dependencies)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("risk_score"), self.volatility_limit)
        self.assertEqual(result.get("status"), "success")

    def test_start_new_handles_missing_keys_gracefully(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {}

        mock_collector = MagicMock()
        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_collector_agent": mock_collector
        }

        result = start_new(dependencies)
        self.assertIsInstance(result, dict)
        self.assertIsNone(result.get("portfolio_id"))

    def test_start_new_stress_testing_aggregation(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio.return_value = {
            "portfolio_id": self.portfolio_id,
            "volatility_limit": self.volatility_limit
        }

        mock_collector = MagicMock()

        mock_stress_reporter = MagicMock()
        mock_stress_reporter.generate_report.return_value = {
            "scenario": self.scenario_name,
            "projected_loss": self.projected_loss
        }

        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_collector_agent": mock_collector,
            "market_portfolio_stress_reporter": mock_stress_reporter
        }

        res = start_new(dependencies)
        self.assertIsInstance(res, dict)
        self.assertTrue(res.get("aggregated"))
        self.assertEqual(res.get("scenario_name"), self.scenario_name)
        self.assertEqual(res.get("loss_value"), self.projected_loss)

    def test_market_portfolio_risk_analytics_hub_class(self):
        hub = MarketPortfolioRiskAnalyticsHub()
        perf_data = {"risk_score": self.volatility_limit}
        stress_data = {"scenario": self.scenario_name, "projected_loss": self.projected_loss}

        with patch("skills.market_portfolio_risk_analytics_hub.db_storage") as mock_db_storage:
            mock_db_storage.save_risk_report.return_value = True

            report = hub.generate_comprehensive_risk_report(self.portfolio_id, perf_data, stress_data)

            self.assertIsInstance(report, dict)
            self.assertEqual(report.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(report.get("risk_score"), self.volatility_limit)
            self.assertEqual(report.get("status"), "success")
            mock_db_storage.save_risk_report.assert_called_once_with(self.portfolio_id, report)

if __name__ == "__main__":
    unittest.main()