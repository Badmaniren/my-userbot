import unittest
import uuid
import random
from skills.market_portfolio_predictive_var_stress_bridge_v3 import PredictiveVarStressBridge
from skills.market_portfolio_predictive_var_engine import InsufficientDataError
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import InvalidDataError

class TestPredictiveVarStressBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.bridge = PredictiveVarStressBridge()
        self.portfolio_id = f"PORTFOLIO_{uuid.uuid4().hex[:8]}"
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.scenario_params = {"volatility_multiplier": round(random.uniform(1.1, 2.5), 2)}
        self.iterations = random.randint(50, 500)
        self.report_id = f"REP_{uuid.uuid4().hex[:8]}"
        self.loss_limit = round(random.uniform(5000.0, 50000.0), 2)

    def tearDown(self):
        self.bridge.cleanup()

    def test_execute_combined_predictive_stress_integration(self):
        result = self.bridge.execute_combined_predictive_stress(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )
        self.assertIsInstance(result, dict)
        self.assertIn("predictive_var", result)
        self.assertIn("monte_carlo_stress", result)

    def test_execute_combined_predictive_stress_fallback_scenario(self):
        invalid_scenario = f"INVALID_{uuid.uuid4().hex[:6]}"
        result = self.bridge.execute_combined_predictive_stress(
            portfolio_id=self.portfolio_id,
            scenario_code=invalid_scenario,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )
        self.assertIsInstance(result, dict)
        self.assertIn("predictive_var", result)
        self.assertIn("monte_carlo_stress", result)

    def test_generate_comprehensive_risk_report_integration(self):
        report = self.bridge.generate_comprehensive_risk_report(
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
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("report_id"), self.report_id)
        self.assertEqual(report.get("loss_limit"), self.loss_limit)
        self.assertIn("predictive_var", report)
        self.assertIn("stress_monte_carlo", report)

    def test_execute_stress_monte_carlo_integration(self):
        mc_result = self.bridge.execute_stress_monte_carlo(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )
        self.assertIsInstance(mc_result, dict)

if __name__ == "__main__":
    unittest.main()