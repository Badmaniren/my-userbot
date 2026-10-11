import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_tax_return_analyzer import (
    PortfolioTaxReturnAnalyzer,
    analyze_portfolio_tax_return
)


class TestMarketPortfolioTaxReturnAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.user_id = uuid.uuid4().hex
        self.symbol = f"{random.choice(['AAPL', 'TSLA', 'GOOG', 'AMZN', 'MSFT'])}_{uuid.uuid4().hex[:6]}"
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.analyzer = PortfolioTaxReturnAnalyzer(storage_file=self.storage_file)

    def test_analyze_portfolio_tax_return_success(self):
        rand_total_return = round(random.uniform(100.0, 5000.0), 2)
        rand_tax_drag = round(random.uniform(10.0, 500.0), 2)
        expected_after_tax = rand_total_return - rand_tax_drag

        with patch("skills.market_portfolio_tax_return_analyzer.PortfolioPerformanceAnalytics") as mock_analytics_cls, \
             patch("skills.market_portfolio_tax_return_analyzer.MarketPortfolioTaxCalculator") as mock_tax_cls:

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.calculate_metrics.return_value = {"total_return": rand_total_return}

            mock_tax_instance = mock_tax_cls.return_value
            mock_tax_instance.calculate_tax.return_value = {"tax_drag": rand_tax_drag}

            result = self.analyzer.analyze_portfolio_tax_return(self.portfolio_id, self.symbol)

            mock_analytics_cls.assert_called_once_with(self.storage_file)
            mock_analytics_instance.calculate_metrics.assert_called_once_with(self.symbol)
            mock_tax_instance.calculate_tax.assert_called_once_with(self.portfolio_id)

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["total_return"], rand_total_return)
            self.assertEqual(result["tax_drag"], rand_tax_drag)
            self.assertEqual(result["after_tax_return"], expected_after_tax)

    def test_evaluate_tax_efficiency_with_portfolio_taxes_method(self):
        rand_deals_count = random.randint(1, 50)
        perf_data = {"metric_score": round(random.uniform(0.1, 1.0), 2)}
        tax_data = {"total_deals": rand_deals_count, "tax_efficiency_score": round(random.uniform(0.5, 1.0), 2)}

        with patch("skills.market_portfolio_tax_return_analyzer.PortfolioPerformanceAnalytics") as mock_analytics_cls, \
             patch("skills.market_portfolio_tax_return_analyzer.MarketPortfolioTaxCalculator") as mock_tax_cls:

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.evaluate_performance.return_value = perf_data

            mock_tax_instance = mock_tax_cls.return_value
            mock_tax_instance.calculate_portfolio_taxes = MagicMock(return_value=tax_data)

            result = self.analyzer.evaluate_tax_efficiency(self.portfolio_id, self.user_id, self.symbol)

            mock_tax_instance.calculate_portfolio_taxes.assert_called_once_with(portfolio_id=self.portfolio_id)
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["deals_evaluated"], rand_deals_count)
            self.assertEqual(result["performance_metrics"], perf_data)
            self.assertEqual(result["tax_data"], tax_data)

    def test_evaluate_tax_efficiency_fallback_to_calculate_tax(self):
        rand_deals_count = random.randint(5, 25)
        perf_data = {"performance_index": round(random.uniform(1.0, 10.0), 2)}
        tax_data = {"total_deals": rand_deals_count}

        with patch("skills.market_portfolio_tax_return_analyzer.PortfolioPerformanceAnalytics") as mock_analytics_cls, \
             patch("skills.market_portfolio_tax_return_analyzer.MarketPortfolioTaxCalculator") as mock_tax_cls:

            mock_analytics_instance = mock_analytics_cls.return_value
            mock_analytics_instance.evaluate_performance.return_value = perf_data

            mock_tax_instance = mock_tax_cls.return_value
            if hasattr(mock_tax_instance, "calculate_portfolio_taxes"):
                delattr(mock_tax_instance, "calculate_portfolio_taxes")
            mock_tax_instance.calculate_tax.return_value = tax_data

            result = self.analyzer.evaluate_tax_efficiency(self.portfolio_id, self.user_id, self.symbol)

            mock_tax_instance.calculate_tax.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["deals_evaluated"], rand_deals_count)
            self.assertEqual(result["performance_metrics"], perf_data)
            self.assertEqual(result["tax_data"], tax_data)

    def test_process_strategy_dividends(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        expected_dividend_result = {"status": "processed", "stream_id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_tax_return_analyzer.MarketPortfolioTaxCalculator") as mock_tax_cls:
            mock_tax_instance = mock_tax_cls.return_value
            mock_tax_instance.process_dividend_stream.return_value = expected_dividend_result

            result = self.analyzer.process_strategy_dividends(stream_data)

            mock_tax_instance.process_dividend_stream.assert_called_once_with(stream_data)
            self.assertEqual(result, expected_dividend_result)

    def test_standalone_analyze_portfolio_tax_return(self):
        rand_total_return = round(random.uniform(500.0, 10000.0), 2)
        rand_tax_drag = round(random.uniform(50.0, 1000.0), 2)
        rand_efficiency = round(random.uniform(0.7, 0.99), 2)

        performance_data = {"total_return": rand_total_return}
        tax_data = {
            "tax_drag": rand_tax_drag,
            "tax_efficiency_score": rand_efficiency
        }

        result = analyze_portfolio_tax_return(self.portfolio_id, performance_data, tax_data)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["total_return"], rand_total_return)
        self.assertEqual(result["tax_drag"], rand_tax_drag)
        self.assertEqual(result["after_tax_return"], rand_total_return - rand_tax_drag)
        self.assertEqual(result["tax_efficiency_score"], rand_efficiency)


if __name__ == "__main__":
    unittest.main()