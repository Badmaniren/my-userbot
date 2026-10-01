import unittest
import os
import uuid
import json
import random
from skills.market_portfolio_var_risk_optimizer import market_portfolio_var_risk_optimizer
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage

class TestIntegrationVaRRiskOptimizer(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        self.asset_name = f"ASSET_{uuid.uuid4().hex[:4]}"
        self.filename = f"audit_report_{uuid.uuid4().hex[:8]}.json"
        self.optimizer = market_portfolio_var_risk_optimizer(portfolio_id=self.portfolio_id, threshold=0.01)

    def tearDown(self):
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except OSError:
                pass

    def test_full_var_optimization_and_audit_flow(self):
        tickers = [f"TICK_{uuid.uuid4().hex[:4]}", f"TICK_{uuid.uuid4().hex[:4]}"]
        random_weight = round(random.uniform(0.1, 0.9), 4)

        weight_update_res = self.optimizer.adjust_asset_weight(self.asset_name, random_weight)
        self.assertTrue(weight_update_res)

        var_val = self.optimizer.calculate_monte_carlo_var(confidence=0.95, simulations=100)
        self.assertIsInstance(var_val, float)
        self.assertGreaterEqual(var_val, 0.0)

        monte_carlo_data = [random.uniform(-0.05, 0.05) for _ in range(50)]
        optimized_result = self.optimizer.optimize_weights(
            portfolio_id=self.portfolio_id,
            tickers=tickers,
            monte_carlo_data=monte_carlo_data,
            confidence_level=0.95
        )

        self.assertIn("optimized_weights", optimized_result)
        self.assertIn("calculated_var", optimized_result)
        for ticker in tickers:
            self.assertIn(ticker, optimized_result["optimized_weights"])

        opt_success = self.optimizer.optimize_portfolio()
        self.assertTrue(opt_success)

        export_res = self.optimizer.export_audit_report(self.portfolio_id, self.filename)
        self.assertTrue(export_res)
        self.assertTrue(os.path.exists(self.filename))

        with open(self.filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()
