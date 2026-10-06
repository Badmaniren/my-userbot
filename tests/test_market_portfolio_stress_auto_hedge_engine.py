import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_auto_hedge_engine import start_new, run_stress_auto_hedge_engine
from skills import db_storage


class TestMarketPortfolioStressAutoHedgeEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.strategy = f"strat_{uuid.uuid4().hex[:6]}"
        self.risk_tolerance = round(random.uniform(0.01, 0.5), 4)

    def test_start_new_anomaly_trigger(self):
        anomaly_val = f"anomaly_res_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_anomaly_detector.detect", return_value=True) as mock_detect, \
             patch("skills.market_portfolio_autonomous_sentinel.process", return_value=anomaly_val) as mock_sentinel:

            res = start_new(self.portfolio_id, self.strategy, self.risk_tolerance)
            self.assertEqual(res, anomaly_val)
            mock_detect.assert_called_once_with(portfolio_id=self.portfolio_id)
            mock_sentinel.assert_called_once_with(self.portfolio_id)

    def test_start_new_stream_io_handling(self):
        stream_val = f"stream_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_anomaly_detector.detect", return_value=False), \
             patch("skills.market_portfolio_collector_agent.fetch_stream", return_value=stream_val) as mock_stream:

            res = start_new(self.portfolio_id, self.strategy, self.risk_tolerance)
            self.assertEqual(res, stream_val)
            mock_stream.assert_called_once_with(self.portfolio_id)

    def test_start_new_audit_logging(self):
        event_id = f"evt_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_anomaly_detector.detect", return_value=False), \
             patch("skills.market_portfolio_collector_agent.fetch_stream", return_value=None), \
             patch("skills.market_portfolio_audit_log_exporter.export_event", return_value=event_id) as mock_export:

            res = start_new(self.portfolio_id, self.strategy, self.risk_tolerance)
            self.assertEqual(res, event_id)
            mock_export.assert_called_once_with(portfolio_id=self.portfolio_id, strategy=self.strategy)

    def test_start_new_exception_resilience(self):
        with patch("skills.market_anomaly_detector.detect", return_value=False), \
             patch("skills.market_portfolio_collector_agent.fetch_stream", return_value=None), \
             patch("skills.market_portfolio_audit_log_exporter.export_event", return_value=None), \
             patch("skills.market_portfolio_api_gateway.connect") as mock_connect, \
             patch("skills.market_portfolio_scenario_simulator.evaluate", return_value=None):

            res = start_new(self.portfolio_id, self.strategy, self.risk_tolerance)
            self.assertTrue(res)
            mock_connect.assert_called_once_with(self.portfolio_id)

    def test_start_new_success_execution(self):
        eval_data = {"eval_id": uuid.uuid4().hex}
        pipeline_res = f"pipeline_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_anomaly_detector.detect", return_value=False), \
             patch("skills.market_portfolio_collector_agent.fetch_stream", return_value=None), \
             patch("skills.market_portfolio_audit_log_exporter.export_event", return_value=None), \
             patch("skills.market_portfolio_api_gateway.connect"), \
             patch("skills.market_portfolio_scenario_simulator.evaluate", return_value=eval_data) as mock_eval, \
             patch("skills.market_portfolio_stress_auto_hedge_engine.market_portfolio_execution_pipeline", return_value=pipeline_res) as mock_pipe:

            res = start_new(self.portfolio_id, self.strategy, self.risk_tolerance)
            self.assertEqual(res, pipeline_res)
            mock_eval.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                strategy=self.strategy,
                risk_tolerance=self.risk_tolerance
            )
            mock_pipe.assert_called_once_with(eval_data)

    def test_db_storage_hedge_order_methods(self):
        order_id = f"ord_{uuid.uuid4().hex[:6]}"
        order_data = {"type": "CALL_OPTION", "portfolio_id": self.portfolio_id}

        db_storage.save_hedge_order(order_id, order_data)
        fetched = db_storage.get_hedge_order_by_id(order_id)
        self.assertEqual(fetched, order_data)


class TestMarketPortfolioStressAutoHedgeIntegration(unittest.TestCase):

    def test_run_stress_auto_hedge_engine_integration(self):
        portfolio_id = f"port_int_{uuid.uuid4().hex[:6]}"
        scenario_data = {"scenario_name": f"drop_{uuid.uuid4().hex[:4]}"}
        monte_carlo_data = {"var_99": random.uniform(1000, 50000)}
        capital = round(random.uniform(10000, 1000000), 2)

        result = run_stress_auto_hedge_engine(portfolio_id, scenario_data, monte_carlo_data, capital)

        self.assertIn("hedge_orders", result)
        self.assertIn("report_file_path", result)
        self.assertTrue(len(result["hedge_orders"]) > 0)

        order = result["hedge_orders"][0]
        self.assertEqual(order["portfolio_id"], portfolio_id)
        self.assertEqual(order["type"], "PUT_OPTION")
        self.assertEqual(order["capital_allocated"], capital * 0.05)


if __name__ == "__main__":
    unittest.main()