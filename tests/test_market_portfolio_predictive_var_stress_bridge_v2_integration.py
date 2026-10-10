import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_stress_bridge_v2 import PredictiveVarStressBridgeV2
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine

class TestPredictiveVarStressBridgeV2Integration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.portfolio_value = round(random.uniform(100000.0, 5000000.0), 2)
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.95, 0.99), 4)
        self.iterations = random.randint(50, 500)
        
        self.scenario_params = {
            "volatility_multiplier": round(random.uniform(1.1, 3.0), 2),
            "market_shock": round(random.uniform(-0.3, -0.05), 4)
        }
        
        self.db_storage = None
        self.extractor_tool = None
        self.market_anomaly_detector = None

        self.var_engine = PredictiveVarEngine(
            db_storage=self.db_storage,
            extractor_tool=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector
        )
        self.monte_carlo_engine = MonteCarloStressEngine()
        
        self.bridge = PredictiveVarStressBridgeV2(
            var_engine=self.var_engine,
            monte_carlo_engine=self.monte_carlo_engine
        )

    def test_end_to_end_predictive_stress_bridge_composition(self):
        try:
            combined_risk_metrics = self.bridge.execute_bridge_pipeline(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                portfolio_value=self.portfolio_value,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                scenario_params=self.scenario_params,
                iterations=self.iterations
            )
        except Exception as e:
            self.fail(f"Integration pipeline execution failed with exception: {e}")

        self.assertIsInstance(combined_risk_metrics, dict)
        self.assertIn("portfolio_id", combined_risk_metrics)
        self.assertEqual(combined_risk_metrics["portfolio_id"], self.portfolio_id)
        
        self.assertIn("predictive_var", combined_risk_metrics)
        self.assertIn("monte_carlo_stress", combined_risk_metrics)
        self.assertIn("integrated_risk_score", combined_risk_metrics)
        
        report_id = str(uuid.uuid4())
        loss_limit = round(random.uniform(10000.0, 50000.0), 2)
        
        try:
            audit_result = self.bridge.export_integrated_audit_report(
                report_id=report_id,
                loss_limit=loss_limit,
                metrics=combined_risk_metrics
            )
        except Exception as e:
            self.fail(f"Integrated audit export failed with exception: {e}")

        self.assertIsInstance(audit_result, dict)
        self.assertIn("report_id", audit_result)
        self.assertEqual(audit_result["report_id"], report_id)

if __name__ == "__main__":
    unittest.main()