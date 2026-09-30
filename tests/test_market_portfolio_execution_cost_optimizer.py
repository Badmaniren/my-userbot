import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_execution_cost_optimizer import (
    MarketPortfolioExecutionCostOptimizer
)

class TestMarketPortfolioExecutionCostOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = MarketPortfolioExecutionCostOptimizer()

    def test_optimize_execution_cost_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_asset = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_volume = round(random.uniform(1000.0, 1000000.0), 2)
        rand_threshold = round(random.uniform(0.001, 0.05), 4)

        mock_slippage_model = MagicMock()
        mock_slippage_model.calculate.return_value = rand_threshold

        with patch('skills.market_portfolio_execution_cost_optimizer.market_portfolio_slippage_model', mock_slippage_model):
            result = self.optimizer.optimize_execution_cost(
                portfolio_id=rand_portfolio_id,
                asset=rand_asset,
                volume=rand_volume
            )

        self.assertIn("optimized_cost", result)
        self.assertIn("status", result)
        self.assertEqual(result["asset"], rand_asset)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertIsInstance(result["optimized_cost"], float)

    def test_liquidity_monitoring_anomaly(self):
        rand_market_id = uuid.uuid4().hex
        rand_stream_data = f"stream_{uuid.uuid4().hex}".encode('utf-8')

        mock_detector = MagicMock()
        mock_detector.analyze_stream.return_value = {"anomaly_detected": True, "severity": "HIGH"}

        with patch('skills.market_portfolio_execution_cost_optimizer.market_anomaly_detector', mock_detector):
            with patch('skills.market_portfolio_execution_cost_optimizer.market_parser') as mock_parser:
                mock_parser.read_stream.return_value = io.BytesIO(rand_stream_data)
                
                evaluation = self.optimizer.monitor_liquidity(market_id=rand_market_id)

        self.assertTrue(evaluation.get("alert_triggered"))
        self.assertEqual(evaluation.get("market_id"), rand_market_id)

    def test_execution_pipeline_integration(self):
        rand_order_id = uuid.uuid4().hex
        rand_price = round(random.uniform(10.0, 1500.0), 2)

        mock_pipeline = MagicMock()
        mock_pipeline.execute_batch.return_value = {"order_id": rand_order_id, "executed_price": rand_price, "success": True}

        with patch('skills.market_portfolio_execution_cost_optimizer.market_portfolio_execution_pipeline', mock_pipeline):
            response = self.optimizer.route_to_execution_pipeline(
                order_id=rand_order_id,
                target_price=rand_price
            )

        self.assertTrue(response["success"])
        self.assertEqual(response["order_id"], rand_order_id)
        self.assertEqual(response["executed_price"], rand_price)

    def test_audit_log_exporter_failure_handling(self):
        rand_event_id = uuid.uuid4().hex
        rand_error_msg = f"ERR_{uuid.uuid4().hex}"

        mock_exporter = MagicMock()
        mock_exporter.export.side_effect = Exception(rand_error_msg)

        with patch('skills.market_portfolio_execution_cost_optimizer.market_portfolio_audit_log_exporter', mock_exporter):
            with self.assertRaises(Exception) as ctx:
                self.optimizer.flush_audit_logs(event_id=rand_event_id)

        self.assertIn(rand_error_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()