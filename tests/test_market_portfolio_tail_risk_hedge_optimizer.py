import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

try:
    import requests
except ImportError:
    requests = None

from skills.market_portfolio_tail_risk_hedge_optimizer import (
    optimize_tail_risk_hedges,
    fetch_and_parse_market_tail_payload,
    evaluate_anomaly_triggers,
    market_portfolio_tail_risk_hedge_optimizer,
    TailRiskHedgeOptimizerException
)


class TestMarketPortfolioTailRiskHedgeOptimizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.confidence = round(random.uniform(0.90, 0.99), 2)
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.market_segment = f"segment_{uuid.uuid4().hex[:8]}"

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_stress_monte_carlo_engine")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_scenario_simulator")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.db_storage")
    def test_optimize_tail_risk_hedges_success(self, mock_db_storage, mock_scenario_simulator, mock_monte_carlo):
        sim_result = {"sim_id": uuid.uuid4().hex, "var": random.random()}
        stress_result = {"stress_score": random.randint(1, 100)}

        mock_monte_carlo.run_simulation.return_value = sim_result
        mock_scenario_simulator.generate_stress_matrix.return_value = stress_result

        result = optimize_tail_risk_hedges(self.portfolio_id, self.confidence)

        mock_monte_carlo.run_simulation.assert_called_once_with(
            portfolio_id=self.portfolio_id, confidence=self.confidence
        )
        mock_scenario_simulator.generate_stress_matrix.assert_called_once_with(self.portfolio_id)
        mock_db_storage.save_hedge_profile.assert_called_once()

        self.assertEqual(result["target_portfolio"], self.portfolio_id)
        self.assertEqual(result["simulation_data"], sim_result)
        self.assertEqual(result["stress_matrix"], stress_result)
        self.assertIn("optimal_hedge_ratio", result)

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_stress_monte_carlo_engine")
    def test_optimize_tail_risk_hedges_portfolio_not_found(self, mock_monte_carlo):
        error_msg = f"Portfolio {self.portfolio_id} not found"
        mock_monte_carlo.run_simulation.side_effect = Exception(error_msg)

        with self.assertRaises(TailRiskHedgeOptimizerException) as ctx:
            optimize_tail_risk_hedges(self.portfolio_id, self.confidence)
        self.assertIn(error_msg, str(ctx.exception))

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_stress_monte_carlo_engine")
    def test_optimize_tail_risk_hedges_simulation_failed(self, mock_monte_carlo):
        error_msg = uuid.uuid4().hex
        mock_monte_carlo.run_simulation.side_effect = Exception(error_msg)

        with self.assertRaises(TailRiskHedgeOptimizerException) as ctx:
            optimize_tail_risk_hedges(self.portfolio_id, self.confidence)
        self.assertIn("Simulation failed", str(ctx.exception))

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.requests.get")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_parser")
    def test_fetch_and_parse_market_tail_payload_success(self, mock_parser, mock_requests_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        expected_parsed = {"payload_id": uuid.uuid4().hex, "status": "parsed"}
        mock_parser.parse_stream.return_value = expected_parsed

        stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        result = fetch_and_parse_market_tail_payload(self.url, stream)

        mock_requests_get.assert_called_once_with(self.url, timeout=10)
        mock_parser.parse_stream.assert_called_once_with(stream)
        self.assertEqual(result, expected_parsed)

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.requests.get")
    def test_fetch_and_parse_market_tail_payload_http_error(self, mock_requests_get):
        if requests is None:
            self.skipTest("requests module not installed")
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_requests_get.return_value = mock_response

        stream = io.BytesIO(b"")
        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_and_parse_market_tail_payload(self.url, stream)

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_anomaly_detector")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_alert_dispatcher")
    def test_evaluate_anomaly_triggers_triggered(self, mock_alert_dispatcher, mock_anomaly_detector):
        code = f"CODE_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["HIGH", "CRITICAL", "WARNING"])
        mock_anomaly_detector.check_anomalies.return_value = {
            "status": "TRIGGERED",
            "code": code,
            "severity": severity
        }

        triggered = evaluate_anomaly_triggers(self.market_segment)

        self.assertTrue(triggered)
        mock_anomaly_detector.check_anomalies.assert_called_once_with(self.market_segment)
        mock_alert_dispatcher.dispatch_alert.assert_called_once_with(code, severity)

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_anomaly_detector")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_alert_dispatcher")
    def test_evaluate_anomaly_triggers_normal(self, mock_alert_dispatcher, mock_anomaly_detector):
        mock_anomaly_detector.check_anomalies.return_value = {
            "status": "NORMAL",
            "code": "OK",
            "severity": "NONE"
        }

        triggered = evaluate_anomaly_triggers(self.market_segment)

        self.assertFalse(triggered)
        mock_anomaly_detector.check_anomalies.assert_called_once_with(self.market_segment)
        mock_alert_dispatcher.dispatch_alert.assert_not_called()

    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_stress_monte_carlo_engine")
    @patch("skills.market_portfolio_tail_risk_hedge_optimizer.market_portfolio_scenario_simulator")
    def test_market_portfolio_tail_risk_hedge_optimizer_payload(self, mock_scenario_simulator, mock_monte_carlo):
        sim_data_val = {"simulation_metric": random.random()}
        stress_matrix_val = {"stress": uuid.uuid4().hex}

        mock_monte_carlo.run_simulation.return_value = sim_data_val
        mock_scenario_simulator.generate_stress_matrix.return_value = stress_matrix_val

        payload = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence
        }

        result = market_portfolio_tail_risk_hedge_optimizer(payload)

        mock_monte_carlo.run_simulation.assert_called_once_with(
            portfolio_id=self.portfolio_id, confidence=self.confidence
        )
        mock_scenario_simulator.generate_stress_matrix.assert_called_once_with(self.portfolio_id)

        self.assertIn("optimal_hedges", result)
        self.assertIn("expected_tail_loss_reduction", result)
        self.assertEqual(result["simulation_data"], sim_data_val)
        self.assertEqual(result["stress_matrix"], stress_matrix_val)


if __name__ == "__main__":
    unittest.main()