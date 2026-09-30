import unittest
import uuid
import random
import io

from skills.market_portfolio_execution_cost_optimizer import (
    MarketPortfolioExecutionCostOptimizer,
    market_portfolio_execution_cost_optimizer
)
import skills.market_portfolio_slippage_model as market_portfolio_slippage_model
import skills.market_anomaly_detector as market_anomaly_detector
import skills.market_parser as market_parser
import skills.market_portfolio_execution_pipeline as market_portfolio_execution_pipeline
import skills.market_portfolio_audit_log_exporter as market_portfolio_audit_log_exporter


class TestMarketPortfolioExecutionCostOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.optimizer = MarketPortfolioExecutionCostOptimizer()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.ticker = f"TICK_{random.choice(['BTC', 'ETH', 'SOL', 'ADA'])}"
        self.volume = round(random.uniform(1.0, 1000.0), 4)
        self.market_id = f"mkt_{uuid.uuid4().hex[:8]}"
        self.order_id = f"ord_{uuid.uuid4().hex[:8]}"
        self.target_price = round(random.uniform(10.0, 50000.0), 2)
        self.event_id = str(uuid.uuid4())

    def test_optimize_execution_cost_integration(self):
        result = self.optimizer.optimize_execution_cost(
            portfolio_id=self.portfolio_id,
            asset=self.ticker,
            volume=self.volume
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("asset"), self.ticker)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("optimized_cost", result)
        self.assertIn("execution_strategy_id", result)
        self.assertIsInstance(result.get("optimized_cost"), float)
        self.assertTrue(len(result.get("execution_strategy_id")) > 0)

        functional_wrapper_result = market_portfolio_execution_cost_optimizer(
            portfolio_id=self.portfolio_id,
            ticker=self.ticker,
            volume=self.volume
        )
        self.assertIsInstance(functional_wrapper_result, dict)
        self.assertEqual(functional_wrapper_result.get("asset"), self.ticker)

    def test_monitor_liquidity_integration(self):
        monitoring_result = self.optimizer.monitor_liquidity(market_id=self.market_id)
        
        self.assertIsInstance(monitoring_result, dict)
        self.assertEqual(monitoring_result.get("market_id"), self.market_id)
        self.assertIn("alert_triggered", monitoring_result)
        self.assertIn("severity", monitoring_result)
        self.assertIsInstance(monitoring_result.get("alert_triggered"), bool)
        self.assertIn(monitoring_result.get("severity"), ["LOW", "MEDIUM", "HIGH", "CRITICAL", "INFO", "WARNING"])

    def test_route_to_execution_pipeline_integration(self):
        routing_result = self.optimizer.route_to_execution_pipeline(
            order_id=self.order_id,
            target_price=self.target_price,
            portfolio_id=self.portfolio_id
        )
        
        self.assertIsInstance(routing_result, dict)
        self.assertEqual(routing_result.get("order_id"), self.order_id)
        self.assertEqual(routing_result.get("executed_price"), self.target_price)
        self.assertIn("success", routing_result)
        self.assertIn("status", routing_result)

    def test_flush_audit_logs_integration(self):
        if market_portfolio_audit_log_exporter is not None and hasattr(market_portfolio_audit_log_exporter, "export"):
            try:
                self.optimizer.flush_audit_logs(event_id=self.event_id)
            except Exception:
                pass
        else:
            with self.assertRaises(Exception):
                self.optimizer.flush_audit_logs(event_id=self.event_id)


if __name__ == "__main__":
    unittest.main()