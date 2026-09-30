import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_execution_cost_optimizer import (
    MarketPortfolioExecutionCostOptimizer,
    market_portfolio_execution_cost_optimizer,
)


class TestMarketPortfolioExecutionCostOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = MarketPortfolioExecutionCostOptimizer()

    def test_optimize_execution_cost_default(self):
        rand_portfolio = uuid.uuid4().hex
        rand_ticker = uuid.uuid4().hex
        rand_volume = random.uniform(1.0, 1000.0)

        with patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_slippage_model") as mock_slippage:
            mock_slippage.calculate.return_value = random.uniform(0.01, 5.0)
            res = self.optimizer.optimize_execution_cost(
                portfolio_id=rand_portfolio,
                ticker=rand_ticker,
                volume=rand_volume
            )

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], rand_portfolio)
        self.assertEqual(res["asset"], rand_ticker)
        self.assertEqual(res["status"], "success")
        self.assertIn("optimized_cost", res)
        self.assertIn("execution_strategy_id", res)

    def test_optimize_execution_cost_with_numeric_output(self):
        rand_asset = uuid.uuid4().hex
        rand_cost = random.uniform(10.0, 500.0)

        res = self.optimizer.optimize_execution_cost(
            asset=rand_asset,
            slippage_model_output=rand_cost
        )

        self.assertEqual(res["optimized_cost"], float(rand_cost))
        self.assertEqual(res["asset"], rand_asset)

    def test_optimize_execution_cost_with_dict_output(self):
        rand_asset = uuid.uuid4().hex
        rand_cost = random.uniform(5.0, 100.0)
        output_dict = {"cost": rand_cost}

        res = self.optimizer.optimize_execution_cost(
            asset=rand_asset,
            slippage_model_output=output_dict
        )

        self.assertEqual(res["optimized_cost"], float(rand_cost))

    def test_monitor_liquidity_anomaly_triggered(self):
        rand_market_id = uuid.uuid4().hex
        rand_severity = random.choice(["HIGH", "MEDIUM", "CRITICAL"])

        with patch("skills.market_portfolio_execution_cost_optimizer.market_anomaly_detector") as mock_detector, \
             patch("skills.market_portfolio_execution_cost_optimizer.market_parser") as mock_parser:
            
            mock_parser.read_stream.return_value = io.BytesIO(uuid.uuid4().bytes)
            mock_detector.analyze_stream.return_value = {
                "anomaly_detected": True,
                "severity": rand_severity
            }

            res = self.optimizer.monitor_liquidity(market_id=rand_market_id)

        self.assertTrue(res["alert_triggered"])
        self.assertEqual(res["market_id"], rand_market_id)
        self.assertEqual(res["severity"], rand_severity)

    def test_monitor_liquidity_no_anomaly(self):
        rand_market_id = uuid.uuid4().hex

        with patch("skills.market_portfolio_execution_cost_optimizer.market_anomaly_detector") as mock_detector, \
             patch("skills.market_portfolio_execution_cost_optimizer.market_parser") as mock_parser:
            
            mock_parser.read_stream.return_value = io.BytesIO(uuid.uuid4().bytes)
            mock_detector.analyze_stream.return_value = {
                "anomaly_detected": False,
                "severity": "LOW"
            }

            res = self.optimizer.monitor_liquidity(market_id=rand_market_id)

        self.assertFalse(res["alert_triggered"])
        self.assertEqual(res["market_id"], rand_market_id)
        self.assertEqual(res["severity"], "LOW")

    def test_route_to_execution_pipeline_with_batch(self):
        rand_order_id = uuid.uuid4().hex
        rand_price = random.uniform(100.0, 2000.0)
        expected_pipeline_result = {"success": True, "order_id": rand_order_id, "status": "batched"}

        with patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_execution_pipeline") as mock_pipeline:
            mock_pipeline.execute_batch.return_value = expected_pipeline_result

            res = self.optimizer.route_to_execution_pipeline(
                order_id=rand_order_id,
                target_price=rand_price
            )

        self.assertEqual(res, expected_pipeline_result)

    def test_route_to_execution_pipeline_fallback(self):
        rand_order_id = uuid.uuid4().hex
        rand_price = random.uniform(1.0, 50.0)

        with patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_execution_pipeline") as mock_pipeline:
            mock_pipeline.execute_batch.return_value = None

            res = self.optimizer.route_to_execution_pipeline(
                order_id=rand_order_id,
                target_price=rand_price
            )

        self.assertTrue(res["success"])
        self.assertEqual(res["order_id"], rand_order_id)
        self.assertEqual(res["executed_price"], rand_price)
        self.assertEqual(res["status"], "dispatched")

    def test_flush_audit_logs_success(self):
        rand_event_id = uuid.uuid4().hex

        with patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_audit_log_exporter") as mock_exporter:
            mock_exporter.export.return_value = True

            try:
                self.optimizer.flush_audit_logs(event_id=rand_event_id)
            except Exception as e:
                self.fail(f"flush_audit_logs raised unexpected exception: {e}")

            mock_exporter.export.assert_called_once_with(rand_event_id)

    def test_flush_audit_logs_exception(self):
        rand_event_id = uuid.uuid4().hex

        with patch("skills.market_portfolio_execution_cost_optimizer.market_portfolio_audit_log_exporter", None):
            with self.assertRaises(Exception) as ctx:
                self.optimizer.flush_audit_logs(event_id=rand_event_id)
            
            self.assertIn(rand_event_id, str(ctx.exception))

    def test_module_level_wrapper_function(self):
        rand_portfolio = uuid.uuid4().hex
        rand_ticker = uuid.uuid4().hex
        rand_volume = random.uniform(10.0, 500.0)

        res = market_portfolio_execution_cost_optimizer(
            portfolio_id=rand_portfolio,
            ticker=rand_ticker,
            volume=rand_volume
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], rand_portfolio)
        self.assertEqual(res["asset"], rand_ticker)
        self.assertEqual(res["status"], "success")


if __name__ == "__main__":
    unittest.main()