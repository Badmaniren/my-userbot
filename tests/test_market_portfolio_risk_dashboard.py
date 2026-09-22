import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_portfolio_risk_dashboard import (
    MarketPortfolioRiskDashboard,
    generate_risk_dashboard
)


class TestMarketPortfolioRiskDashboard(unittest.TestCase):

    def test_market_portfolio_risk_dashboard_success(self):
        storage_file = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{random.randint(100, 999)}"

        mock_metrics = {"volatility": random.random(), "sharpe": random.uniform(0.5, 2.5)}
        mock_performance = {"return": random.uniform(-0.1, 0.3), "alpha": random.uniform(0.01, 0.05)}
        mock_ascii_chart = f"CHART_DATA_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_risk_dashboard.PortfolioPerformanceAnalytics") as mock_analytics_cls, \
             patch("skills.market_portfolio_risk_dashboard.PortfolioVisualizer") as mock_visualizer_cls:

            instance_analytics = mock_analytics_cls.return_value
            instance_analytics.calculate_metrics.return_value = mock_metrics
            instance_analytics.evaluate_performance.return_value = mock_performance

            instance_visualizer = mock_visualizer_cls.return_value
            instance_visualizer.generate_ascii_chart.return_value = mock_ascii_chart

            dashboard = generate_risk_dashboard(storage_file, symbol)

            mock_analytics_cls.assert_called_once_with(storage_file)
            mock_visualizer_cls.assert_called_once_with(storage_file)

            instance_analytics.load_data.assert_called_once()
            instance_visualizer.load_data.assert_called_once()

            instance_analytics.calculate_metrics.assert_called_once_with(symbol)
            instance_analytics.evaluate_performance.assert_called_once_with(symbol)
            instance_visualizer.generate_ascii_chart.assert_called_once_with(symbol)

            self.assertIn(symbol, dashboard)
            self.assertIn(str(mock_metrics), dashboard)
            self.assertIn(str(mock_performance), dashboard)
            self.assertIn(mock_ascii_chart, dashboard)

    def test_market_portfolio_risk_dashboard_empty(self):
        storage_file = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{random.randint(1000, 9999)}"

        with patch("skills.market_portfolio_risk_dashboard.PortfolioPerformanceAnalytics") as mock_analytics_cls, \
             patch("skills.market_portfolio_risk_dashboard.PortfolioVisualizer") as mock_visualizer_cls:

            instance_analytics = mock_analytics_cls.return_value
            instance_analytics.calculate_metrics.return_value = {}
            instance_analytics.evaluate_performance.return_value = {}

            instance_visualizer = mock_visualizer_cls.return_value
            instance_visualizer.generate_ascii_chart.return_value = ""

            dashboard = generate_risk_dashboard(storage_file, symbol)

            self.assertEqual(dashboard, {})

    def test_market_portfolio_risk_dashboard_missing_load_data(self):
        storage_file = f"storage_{uuid.uuid4().hex}.db"
        symbol = f"SYM_{random.randint(100, 999)}"

        mock_metrics = {"risk": random.random()}
        mock_performance = {"score": random.randint(1, 100)}
        mock_ascii_chart = f"ASCII_{uuid.uuid4().hex}"

        class DummyAnalyticsWithoutLoad:
            def __init__(self, sf):
                self.sf = sf
            def calculate_metrics(self, sym):
                return mock_metrics
            def evaluate_performance(self, sym):
                return mock_performance

        class DummyVisualizerWithoutLoad:
            def __init__(self, sf):
                self.sf = sf
            def generate_ascii_chart(self, sym):
                return mock_ascii_chart

        with patch("skills.market_portfolio_risk_dashboard.PortfolioPerformanceAnalytics", DummyAnalyticsWithoutLoad), \
             patch("skills.market_portfolio_risk_dashboard.PortfolioVisualizer", DummyVisualizerWithoutLoad):

            dashboard_obj = MarketPortfolioRiskDashboard(storage_file)
            result = dashboard_obj.generate_dashboard(symbol)

            self.assertIn(symbol, result)
            self.assertIn(str(mock_metrics), result)
            self.assertIn(str(mock_performance), result)
            self.assertIn(mock_ascii_chart, result)


if __name__ == "__main__":
    unittest.main()