import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine, VarEngineError, InsufficientDataError
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine
from skills.market_portfolio_predictive_var_stress_bridge_v4 import PredictiveVarStressBridgeV4

class TestPredictiveVarStressBridgeV4Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.portfolio_value = round(random.uniform(100000.0, 5000000.0), 2)
        self.confidence_level = round(random.choice([0.95, 0.99]), 2)
        self.horizon_days = random.randint(10, 30)
        self.simulations = random.randint(1000, 5000)
        self.iterations = random.randint(50, 200)
        self.loss_limit = round(random.uniform(10000.0, 50000.0), 2)
        self.report_id = str(uuid.uuid4())

        self.scenario_params = {
            "volatility_multiplier": round(random.uniform(1.1, 3.0), 2),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }

        self.db_storage = None
        self.extractor_tool = None
        self.market_anomaly_detector = None

        self.predictive_engine = PredictiveVarEngine(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector
        )
        self.monte_carlo_engine = MonteCarloStressEngine()

        self.bridge = PredictiveVarStressBridgeV4(
            predictive_engine=self.predictive_engine,
            monte_carlo_engine=self.monte_carlo_engine
        )

    def test_end_to_end_stress_testing_composition(self):
        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"

        with patch('requests.get', return_value=mock_response):
            bridge_result = self.bridge.execute_end_to_end_stress_test(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                simulations=self.simulations,
                iterations=self.iterations
            )

        self.assertIsInstance(bridge_result, dict)
        self.assertIn("predictive_var_result", bridge_result)
        self.assertIn("monte_carlo_result", bridge_result)
        self.assertIn("integrated_risk_score", bridge_result)

    def test_bridge_audit_export_integration(self):
        export_result = self.bridge.export_bridge_audit_report(
            report_id=self.report_id,
            loss_limit=self.loss_limit
        )
        self.assertIsInstance(export_result, dict)
        self.assertEqual(export_result.get("report_id"), self.report_id)

    def test_exception_handling_without_stubs(self):
        invalid_portfolio_id = ""
        with self.assertRaises((VarEngineError, InsufficientDataError, ValueError, Exception)):
            self.bridge.execute_end_to_end_stress_test(
                portfolio_id=invalid_portfolio_id,
                scenario_code=self.scenario_code,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                confidence_level=self.confidence_level,
                horizon_days=self.horizon_days,
                simulations=self.simulations,
                iterations=self.iterations
            )

if __name__ == "__main__":
    unittest.main()