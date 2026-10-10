import unittest
import uuid
import random
import os
from skills.market_portfolio_execution_risk_gate import MarketPortfolioExecutionRiskGate
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline

class TestMarketPortfolioExecutionRiskGateIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.symbol = f"TICK_{random.choice(['AAPL', 'GOOGL', 'TSLA', 'MSFT'])}"
        self.volume = random.randint(100, 5000)
        self.price = round(random.uniform(50.0, 1500.0), 2)
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.export_target = f"export_{uuid.uuid4().hex[:6]}.json"
        self.storage_file = f"storage_{uuid.uuid4().hex[:6]}.db"
        
        self.risk_gate = MarketPortfolioExecutionRiskGate(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass

    def test_risk_gate_composition_and_execution(self):
        order_data = {
            "symbol": self.symbol,
            "volume": self.volume,
            "price": self.price,
            "order_type": random.choice(["LIMIT", "MARKET"]),
            "portfolio_id": self.portfolio_id
        }
        market_context = {
            "volatility": round(random.uniform(0.1, 0.5), 4),
            "liquidity_score": round(random.uniform(1000.0, 50000.0), 2)
        }
        percentage = round(random.uniform(0.01, 0.1), 3)

        result = self.risk_gate.validate_and_execute(
            order_data=order_data,
            market_context=market_context,
            percentage=percentage,
            confidence_level=self.confidence_level,
            export_target=self.export_target
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("var_liquidity_metrics", result)
        self.assertIn("execution_result", result)

        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("symbol"), self.symbol)

        if result.get("status") == "APPROVED":
            self.assertIsNotNone(result.get("execution_result"))
        
        self.assertTrue(os.path.exists(self.storage_file) or result.get("storage_checked", True))

if __name__ == "__main__":
    unittest.main()