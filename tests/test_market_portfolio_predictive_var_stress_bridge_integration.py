import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_stress_bridge import (
    PredictiveVarStressBridge
)
from skills.market_portfolio_predictive_var_engine import (
    PredictiveVarEngine
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine
)


class TestMarketPortfolioPredictiveVarStressBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = f"SCENARIO_{random.randint(1000, 9999)}"
        self.portfolio_value = round(random.uniform(50000.0, 1000000.0), 2)
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.iterations = random.randint(50, 500)
        self.loss_limit = round(random.uniform(10000.0, 50000.0), 2)
        self.report_id = str(uuid.uuid4())

        self.scenario_params = {
            "volatility_multiplier": round(random.uniform(1.1, 3.0), 2),
            "drift": round(random.uniform(-0.05, 0.02), 4)
        }

        db_storage_mock = object()
        extractor_tool_mock = object()
        anomaly_detector_mock = object()

        self.var_engine = PredictiveVarEngine(
            db_storage=db_storage_mock,
            extractor_tool=extractor_tool_mock,
            market_anomaly_detector=anomaly_detector_mock
        )
        self.mc_engine = MonteCarloStressEngine()

        self.bridge = PredictiveVarStressBridge(
            predictive_var_engine=self.var_engine,
            monte_carlo_engine=self.mc_engine
        )

    def test_end_to_end_predictive_stress_workflow(self):
        result = self.bridge.execute_comprehensive_stress_test(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            portfolio_value=self.portfolio_value,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )

        self.assertIsInstance(result, dict)
        self.assertIn("var_metrics", result)
        self.assertIn("monte_carlo_metrics", result)
        self.assertIn("composite_stress_score", result)

        report_export = self.bridge.export_bridge_audit_report(
            report_id=self.report_id,
            loss_limit=self.loss_limit
        )

        self.assertIsInstance(report_export, dict)
        self.assertIn("report_id", report_export)
        self.assertEqual(report_export["report_id"], self.report_id)

        if "report_path" in report_export and report_export["report_path"]:
            self.assertTrue(os.path.exists(report_export["report_path"]))
            os.remove(report_export["report_path"])


if __name__ == "__main__":
    unittest.main()