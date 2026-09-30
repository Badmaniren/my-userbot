import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
from skills.market_portfolio_stress_monte_carlo_resiliency_engine import (
    MarketPortfolioStressMonteCarloResiliencyEngine,
    market_portfolio_stress_monte_carlo_resiliency_engine
)

class TestMarketPortfolioStressMonteCarloResiliencyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MarketPortfolioStressMonteCarloResiliencyEngine()
        self.portfolio_id = str(uuid.uuid4())
        self.iterations = random.randint(100, 1000)
        self.liquidity_shock = round(random.uniform(0.01, 0.5), 4)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.channel = f"chan_{uuid.uuid4().hex[:4]}"
        self.target_class = f"class_{uuid.uuid4().hex[:4]}"
        self.random_content = f"content_{uuid.uuid4().hex}".encode('utf-8')

    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.requests.get')
    def test_run_monte_carlo_simulation_logic(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = f"<html><body>{uuid.uuid4().hex}</body></html>".encode('utf-8')
        mock_get.return_value = mock_response

        result = self.engine.run_monte_carlo_simulation(self.portfolio_id, self.iterations, self.liquidity_shock)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("resiliency_score", result)
        self.assertIn("var_99", result)
        mock_get.assert_called_once()

    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.market_parser')
    def test_evaluate_dynamic_transaction_costs_logic(self, mock_market_parser):
        expected_metric = round(random.uniform(1.0, 100.0), 2)
        mock_market_parser.extract_liquidity_metric.return_value = expected_metric

        stream = io.BytesIO(self.random_content)
        metric = self.engine.evaluate_dynamic_transaction_costs(stream, self.target_class)

        self.assertEqual(metric, expected_metric)
        mock_market_parser.extract_liquidity_metric.assert_called_once_with(self.random_content, self.target_class)

    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.db_storage')
    def test_persist_simulation_state_logic(self, mock_db_storage):
        test_data = {
            "metric": uuid.uuid4().hex,
            "value": random.randint(1, 500)
        }

        self.engine.persist_simulation_state(self.portfolio_id, test_data)

        mock_db_storage.save_simulation_results.assert_called_once_with(self.portfolio_id, test_data)

    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.market_anomaly_detector')
    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.market_portfolio_alert_dispatcher')
    def test_check_and_dispatch_stress_alerts_triggered(self, mock_dispatcher, mock_detector):
        anomaly_code = f"ANOMALY_{random.randint(100, 999)}"
        mock_detector.check_volatility_spike.return_value = anomaly_code

        result = self.engine.check_and_dispatch_stress_alerts(self.symbol, self.channel)

        self.assertTrue(result)
        mock_detector.check_volatility_spike.assert_called_once_with(self.symbol)
        mock_dispatcher.send_alert.assert_called_once_with(self.symbol, self.channel, anomaly_code)

    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.market_anomaly_detector')
    @patch('skills.market_portfolio_stress_monte_carlo_resiliency_engine.market_portfolio_alert_dispatcher')
    def test_check_and_dispatch_stress_alerts_not_triggered(self, mock_dispatcher, mock_detector):
        mock_detector.check_volatility_spike.return_value = None

        result = self.engine.check_and_dispatch_stress_alerts(self.symbol, self.channel)

        self.assertFalse(result)
        mock_detector.check_volatility_spike.assert_called_once_with(self.symbol)
        mock_dispatcher.send_alert.assert_not_called()

    def test_functional_wrapper_with_dict(self):
        sim_count = random.randint(50, 500)
        input_data = {"simulations": sim_count, "other_param": uuid.uuid4().hex}
        result = market_portfolio_stress_monte_carlo_resiliency_engine(input_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["simulations_run"], sim_count)
        self.assertIn("resiliency_score", result)
        self.assertIn("var_99", result)

    def test_functional_wrapper_without_dict(self):
        input_data = uuid.uuid4().hex
        result = market_portfolio_stress_monte_carlo_resiliency_engine(input_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["simulations_run"], 100)
        self.assertIn("resiliency_score", result)
        self.assertIn("var_99", result)

if __name__ == "__main__":
    unittest.main()