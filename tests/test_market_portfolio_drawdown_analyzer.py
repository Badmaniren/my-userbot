import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.market_portfolio_drawdown_analyzer import MarketPortfolioDrawdownAnalyzer, market_portfolio_drawdown_analyzer

class TestMarketPortfolioDrawdownAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.scenario_name = f"scenario_{uuid.uuid4().hex[:8]}"
        self.analyzer = MarketPortfolioDrawdownAnalyzer()

    def test_drawdown_calculation_logic(self):
        dynamic_returns = [round(random.uniform(-0.15, 0.15), 4) for _ in range(10)]
        with patch.object(MarketPortfolioDrawdownAnalyzer, '_fetch_historical_returns', return_value=dynamic_returns) as mock_fetch:
            conf = round(random.uniform(0.90, 0.99), 2)
            result = self.analyzer.analyze_drawdown(self.portfolio_id, confidence=conf)
            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertIn("max_drawdown", result)
            self.assertIn("value_at_risk", result)
            self.assertIn("conditional_var", result)
            self.assertGreaterEqual(result["max_drawdown"], 0.0)

    def test_var_and_cvar_computation_chaos(self):
        random_returns = [round(random.uniform(-0.2, 0.2), 4) for _ in range(15)]
        payload_str = f"id:{self.portfolio_id},returns:{','.join(map(str, random_returns))}"
        stream = io.BytesIO(payload_str.encode('utf-8'))

        alpha = round(random.uniform(0.90, 0.98), 2)
        metrics = self.analyzer.compute_risk_metrics(stream, alpha=alpha)

        self.assertIn("value_at_risk", metrics)
        self.assertIn("conditional_var", metrics)
        self.assertIsInstance(metrics["value_at_risk"], float)
        self.assertIsInstance(metrics["conditional_var"], float)

    def test_stress_scenario_drawdown_integration(self):
        mock_sim = MagicMock()
        expected_dd = round(random.uniform(0.1, 0.5), 2)
        expected_days = random.randint(30, 300)
        mock_sim.run_simulation.return_value = {
            'scenario': self.scenario_name,
            'simulated_max_drawdown': expected_dd,
            'recovery_days_estimate': expected_days
        }

        analyzer_with_sim = MarketPortfolioDrawdownAnalyzer(market_portfolio_scenario_simulator=mock_sim)
        report = analyzer_with_sim.evaluate_stress_scenario(self.portfolio_id, self.scenario_name)

        mock_sim.run_simulation.assert_called_once_with(portfolio_id=self.portfolio_id, scenario_name=self.scenario_name)
        self.assertEqual(report['simulated_max_drawdown'], expected_dd)
        self.assertEqual(report['recovery_days_estimate'], expected_days)

    def test_anomaly_and_alert_trigger(self):
        score = round(random.uniform(0.5, 1.0), 4)
        mock_detector_module = MagicMock()
        mock_detector_module.check_tail_risk.return_value = {
            'triggered': True,
            'anomaly_score': score
        }

        with patch.dict('sys.modules', {'skills.market_anomaly_detector': mock_detector_module}):
            res = self.analyzer.monitor_tail_risks(self.portfolio_id)
            self.assertTrue(res["anomaly_detected"])
            self.assertEqual(res["anomaly_score"], score)

    def test_functional_entrypoint(self):
        shock_val = round(random.uniform(0.05, 0.89), 2)
        payload = {
            "portfolio_id": self.portfolio_id,
            "simulation_data": {
                "shock_factor": shock_val
            }
        }
        res = market_portfolio_drawdown_analyzer(payload)
        self.assertIn("max_drawdown", res)
        self.assertEqual(res["max_drawdown"], float(shock_val))
        self.assertIn("value_at_risk", res)
        self.assertIn("conditional_var", res)

if __name__ == '__main__':
    unittest.main()
