import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_ml_predictor import market_portfolio_stress_audit_ml_predictor, start_new
from skills import db_storage
from skills import market_portfolio_collector_agent
from skills import market_portfolio_stress_audit_exporter_v2
from skills import market_anomaly_detector
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_predictive_aggregator
from skills import market_portfolio_stress_scenario_pipeline
from skills import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressAuditMlPredictorIntegration(unittest.TestCase):

    def test_direct_predictor_flow(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_scenario = {"market_drop": random.uniform(0.1, 0.5)}
        rand_factor = random.random()

        result = market_portfolio_stress_audit_ml_predictor(
            portfolio_id=rand_portfolio_id,
            scenario_data=rand_scenario,
            historical_factor=rand_factor
        )

        self.assertIn("prediction_id", result)
        self.assertIn("stress_probability", result)
        self.assertEqual(result["stress_probability"], float(rand_factor))
        self.assertTrue(result["prediction_id"].endswith(rand_portfolio_id))

    def test_start_new_stream_flow(self):
        stream_name = f"stream_{uuid.uuid4().hex[:6]}"
        payload = {"stream_target": stream_name}

        if market_portfolio_collector_agent is not None and hasattr(market_portfolio_collector_agent, "fetch_stream"):
            stream_data = market_portfolio_collector_agent.fetch_stream(stream_name)
            if market_portfolio_stress_audit_exporter_v2 is not None and hasattr(market_portfolio_stress_audit_exporter_v2, "export"):
                expected_path = market_portfolio_stress_audit_exporter_v2.export(stream_data)

                result = start_new(payload)
                self.assertIsInstance(result, dict)
                self.assertIn("export_path", result)
                if expected_path:
                    self.assertEqual(result["export_path"], expected_path)

    def test_start_new_anomaly_flow(self):
        payload = {
            "anomaly_check": True,
            "metric_value": random.randint(100, 1000)
        }

        if market_anomaly_detector is not None and hasattr(market_anomaly_detector, "detect"):
            anomaly_res = market_anomaly_detector.detect(payload)
            if anomaly_res and isinstance(anomaly_res, dict) and anomaly_res.get("is_anomaly"):
                result = start_new(payload)
                self.assertIsInstance(result, dict)
                self.assertTrue(result.get("anomaly_handled"))

    def test_start_new_predictive_aggregator_flow(self):
        token_name = f"TKN_{uuid.uuid4().hex[:4].upper()}"
        drawdown_val = random.uniform(0.05, 0.45)
        payload = {
            "aggregate_target": token_name,
            "simulated_drawdown": drawdown_val
        }

        if market_portfolio_predictive_aggregator is not None and hasattr(market_portfolio_predictive_aggregator, "aggregate_predictions"):
            result = start_new(payload)
            self.assertIsInstance(result, dict)
            self.assertIn("predicted_token", result)
            self.assertIn("drawdown", result)

    def test_start_new_success_main_flow(self):
        portfolio_id = f"port_main_{uuid.uuid4().hex[:8]}"
        payload = {
            "portfolio_id": portfolio_id,
            "assets": ["BTC", "ETH", "USDT"],
            "allocation": [0.5, 0.3, 0.2]
        }

        result = start_new(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("audit_metrics", result)
        self.assertIsInstance(result["audit_metrics"], dict)

if __name__ == "__main__":
    unittest.main()