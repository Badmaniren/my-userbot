import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_stress_bridge_v3 import PredictiveVarStressBridge
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine

class TestPredictiveVarStressBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.portfolio_value = round(random.uniform(100000.0, 10000000.0), 2)
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.iterations = random.randint(50, 500)
        self.loss_limit = round(random.uniform(10000.0, 500000.0), 2)
        self.report_id = str(uuid.uuid4())
        
        self.scenario_params = {
            "volatility_multiplier": round(random.uniform(1.1, 3.0), 2),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }
        
        self.bridge = PredictiveVarStressBridge()

    def test_bridge_composition_and_execution(self):
        self.assertIsInstance(self.bridge.var_engine, PredictiveVarEngine)
        self.assertIsInstance(self.bridge.mc_engine, MonteCarloStressEngine)

        var_result = self.bridge.execute_predictive_var(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )
        
        self.assertIsInstance(var_result, dict)
        self.assertIn("var_value", var_result)

        stress_result = self.bridge.execute_stress_monte_carlo(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )
        
        self.assertIsInstance(stress_result, dict)
        self.assertIn("simulation_id", stress_result)

        integrated_report = self.bridge.generate_comprehensive_risk_report(
            report_id=self.report_id,
            loss_limit=self.loss_limit,
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )

        self.assertIsInstance(integrated_report, dict)
        self.assertEqual(integrated_report.get("report_id"), self.report_id)
        self.assertIn("predictive_var", integrated_report)
        self.assertIn("stress_monte_carlo", integrated_report)

    def tearDown(self):
        if hasattr(self.bridge, "cleanup") and callable(self.bridge.cleanup):
            self.bridge.cleanup()

if __name__ == "__main__":
    unittest.main()