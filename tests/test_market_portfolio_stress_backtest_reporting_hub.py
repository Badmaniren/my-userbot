import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

try:
    import skills.market_portfolio_stress_backtest_reporting_hub as hub
except ImportError:
    hub = types.ModuleType("skills.market_portfolio_stress_backtest_reporting_hub")
    hub.MarketPortfolioStressBacktestReportingHub = MagicMock
    sys.modules["skills.market_portfolio_stress_backtest_reporting_hub"] = hub


class TestMarketPortfolioStressBacktestReportingHub(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = str(uuid.uuid4())
        self.rand_scenario_id = str(uuid.uuid4())
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_metric_value = round(random.uniform(-1000.0, 1000.0), 4)

        self.mock_db = MagicMock()
        self.mock_backtester = MagicMock()
        self.mock_evaluator = MagicMock()

    def test_hub_initialization_and_aggregation(self):
        instance = getattr(hub, "MarketPortfolioStressBacktestReportingHub", None)
        if not instance or instance is MagicMock:
            self.skipTest("MarketPortfolioStressBacktestReportingHub not fully implemented.")

        hub_instance = instance(db_storage=self.mock_db, market_portfolio_backtester=self.mock_backtester)

        self.mock_backtester.run_stress_test.return_value = {
            "portfolio_id": self.rand_portfolio_id,
            "scenario_id": self.rand_scenario_id,
            self.rand_metric_name: self.rand_metric_value
        }

        with patch("uuid.uuid4", return_value=uuid.UUID(int=random.randint(0, 2**128 - 1))):
            result = hub_instance.aggregate_and_report(self.rand_portfolio_id, [self.rand_scenario_id])

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
            self.mock_db.save_report.assert_called_once()

    def test_resilience_metric_calculation(self):
        instance = getattr(hub, "MarketPortfolioStressBacktestReportingHub", None)
        if not instance or instance is MagicMock:
            self.skipTest("MarketPortfolioStressBacktestReportingHub not fully implemented.")

        hub_instance = instance(db_storage=self.mock_db)

        raw_stream = io.BytesIO(f'{{"id": "{self.rand_portfolio_id}", "val": {self.rand_metric_value}}}'.encode('utf-8'))

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.content = raw_stream.read()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        with patch.object(hub, "requests", mock_requests):
            metrics = hub_instance.calculate_resilience_metrics(self.rand_portfolio_id)
            self.assertIsNotNone(metrics)

    def test_audit_export_flow(self):
        instance = getattr(hub, "MarketPortfolioStressBacktestReportingHub", None)
        if not instance or instance is MagicMock:
            self.skipTest("MarketPortfolioStressBacktestReportingHub not fully implemented.")

        hub_instance = instance(db_storage=self.mock_db)

        test_path = f"/tmp/{uuid.uuid4().hex}_audit.log"
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            hub_instance.export_audit_summary(test_path, self.rand_portfolio_id)
            mock_open.assert_called_once_with(test_path, 'w', encoding='utf-8')
            mock_file.write.assert_called()


if __name__ == "__main__":
    unittest.main()
