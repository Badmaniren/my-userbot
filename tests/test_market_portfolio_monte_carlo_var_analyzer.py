import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io

from skills.market_portfolio_monte_carlo_var_analyzer import (
    MarketPortfolioMonteCarloVarAnalyzer,
    market_portfolio_monte_carlo_var_analyzer_run
)


class TestMarketPortfolioMonteCarloVarAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence = round(random.uniform(0.90, 0.99), 2)
        self.url = f"https://{uuid.uuid4().hex}.com/stream"

    @patch("skills.market_portfolio_monte_carlo_var_analyzer.market_portfolio_stress_monte_carlo_engine_run", create=True)
    def test_analyze_var_with_engine(self, mock_engine_run):
        mock_engine = MagicMock()
        sim_returns = [random.uniform(-0.05, 0.05) for _ in range(50)]
        mock_engine.run_simulation.return_value = sim_returns

        analyzer = MarketPortfolioMonteCarloVarAnalyzer(monte_carlo_engine=mock_engine)
        result = analyzer.analyze_var(self.portfolio_id, self.confidence)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], self.confidence)
        self.assertIn("var", result)
        self.assertIn("cvar", result)
        self.assertGreaterEqual(result["var"], 0.0)
        self.assertGreaterEqual(result["cvar"], 0.0)
        mock_engine.run_simulation.assert_called_once_with(self.portfolio_id)

    def test_analyze_var_empty_simulations(self):
        mock_engine = MagicMock()
        mock_engine.run_simulation.return_value = []

        analyzer = MarketPortfolioMonteCarloVarAnalyzer(monte_carlo_engine=mock_engine)
        with self.assertRaises(ValueError):
            analyzer.analyze_var(self.portfolio_id, self.confidence)

    def test_analyze_var_no_engine(self):
        analyzer = MarketPortfolioMonteCarloVarAnalyzer(monte_carlo_engine=None)
        with self.assertRaises(ValueError):
            analyzer.analyze_var(self.portfolio_id, self.confidence)

    @patch("skills.market_portfolio_monte_carlo_var_analyzer.requests.get")
    def test_fetch_external_monte_carlo_stream(self, mock_requests_get):
        expected_content = uuid.uuid4().hex.encode('utf-8')
        mock_response = MagicMock()
        mock_response.content = expected_content
        mock_requests_get.return_value = mock_response

        analyzer = MarketPortfolioMonteCarloVarAnalyzer()
        content = analyzer.fetch_external_monte_carlo_stream(self.url)

        self.assertEqual(content, expected_content)
        mock_requests_get.assert_called_once_with(self.url, timeout=10)

    def test_runner_function_with_dict(self):
        initial_capital = random.uniform(10000.0, 50000.0)
        final_values = [initial_capital * random.uniform(0.9, 1.1) for _ in range(20)]
        monte_carlo_data = {
            "initial_capital": initial_capital,
            "final_values": final_values
        }

        result = market_portfolio_monte_carlo_var_analyzer_run(
            portfolio_id=self.portfolio_id,
            monte_carlo_data=monte_carlo_data,
            confidence=self.confidence
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], self.confidence)
        self.assertGreaterEqual(result["var"], 0.0)
        self.assertGreaterEqual(result["cvar"], 0.0)

    def test_runner_function_with_iterable(self):
        simulations = [random.uniform(-0.1, 0.1) for _ in range(30)]

        result = market_portfolio_monte_carlo_var_analyzer_run(
            portfolio_id=self.portfolio_id,
            monte_carlo_data=simulations,
            confidence=self.confidence
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["confidence_level"], self.confidence)
        self.assertGreaterEqual(result["var"], 0.0)
        self.assertGreaterEqual(result["cvar"], 0.0)

    def test_runner_function_empty_defaults(self):
        result = market_portfolio_monte_carlo_var_analyzer_run(
            portfolio_id=self.portfolio_id,
            monte_carlo_data=[],
            confidence=self.confidence
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertGreater(result["var"], 0.0)
        self.assertGreater(result["cvar"], 0.0)


if __name__ == "__main__":
    unittest.main()