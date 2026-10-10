import unittest
import uuid
import random
import os
from skills.market_portfolio_execution_risk_gate import MarketPortfolioExecutionRiskGate, ExecutionRiskGateError

class TestMarketPortfolioExecutionRiskGateIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.db"
        self.gate = MarketPortfolioExecutionRiskGate(storage_file=self.storage_file)
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(100, 999)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_validate_and_execute_success(self):
        order_data = {
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "volume": random.randint(10, 500),
            "price": round(random.uniform(10.0, 500.0), 2),
            "order_type": "BUY"
        }
        market_context = {
            "volatility": round(random.uniform(0.01, 0.05), 4),
            "trend": "bullish"
        }
        percentage = round(random.uniform(0.01, 0.1), 2)

        result = self.gate.validate_and_execute(
            order_data=order_data,
            market_context=market_context,
            percentage=percentage,
            confidence_level=0.95,
            var_limit=1000000.0,
            liquidity_limit=-999.0,
            export_target="json"
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "APPROVED")
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("var_liquidity_metrics", result)
        self.assertIn("execution_result", result)

    def test_validate_and_execute_var_breach(self):
        order_data = {
            "portfolio_id": self.portfolio_id,
            "symbol": self.symbol,
            "volume": random.randint(1000, 5000),
            "price": round(random.uniform(100.0, 1000.0), 2)
        }
        market_context = {"volatility": 0.5}

        with self.assertRaises(ExecutionRiskGateError) as context:
            self.gate.validate_and_execute(
                order_data=order_data,
                market_context=market_context,
                var_limit=-1.0,
                liquidity_limit=-999.0
            )
        self.assertIn("VaR limit breached", str(context.exception))

    def test_batch_validate_and_execute_success(self):
        orders = [
            {"symbol": f"SYM{random.randint(10, 99)}", "volume": random.randint(1, 100)}
            for _ in range(random.randint(2, 5))
        ]
        contexts = [
            {"spread": round(random.uniform(0.01, 0.05), 4)}
            for _ in range(len(orders))
        ]
        percentage = 0.05

        batch_result = self.gate.batch_validate_and_execute(
            portfolio_id=self.portfolio_id,
            confidence_level=0.95,
            var_limit=1000000.0,
            liquidity_limit=-999.0,
            orders=orders,
            contexts=contexts,
            percentage=percentage
        )

        self.assertIsInstance(batch_result, list)

if __name__ == "__main__":
    unittest.main()