import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_ml_telemetry_collector import (
    market_portfolio_stress_ml_telemetry_collector
)
from skills.db_storage import db_storage
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    market_portfolio_stress_scenario_matrix_evaluator
)
from skills.market_portfolio_var_liquidity_core import (
    market_portfolio_var_liquidity_core
)

class TestMarketPortfolioStressMlTelemetryCollectorIntegration(unittest.TestCase):
    def test_telemetry_collection_pipeline_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        stress_factor = round(random.uniform(0.05, 0.5), 4)
        volatility_index = round(random.uniform(15.0, 45.0), 2)

        matrix_evaluator_input = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "stress_factor": stress_factor,
            "volatility": volatility_index
        }
        
        matrix_result = market_portfolio_stress_scenario_matrix_evaluator(matrix_evaluator_input)
        
        var_core_input = {
            "portfolio_id": portfolio_id,
            "evaluation_data": matrix_result
        }
        var_result = market_portfolio_var_liquidity_core(var_core_input)

        collector_payload = {
            "telemetry_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "matrix_metrics": matrix_result,
            "var_liquidity_metrics": var_result,
            "ml_feature_weight": random.randint(1, 100)
        }

        collector_output = market_portfolio_stress_ml_telemetry_collector(collector_payload)

        self.assertIsNotNone(collector_output)
        self.assertIn("telemetry_id", collector_output)
        self.assertEqual(collector_output["telemetry_id"], collector_payload["telemetry_id"])
        self.assertEqual(collector_output["portfolio_id"], portfolio_id)

        db_query = {
            "query_type": "get_telemetry",
            "telemetry_id": collector_payload["telemetry_id"]
        }
        db_record = db_storage(db_query)

        self.assertIsNotNone(db_record)
        self.assertEqual(db_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(db_record.get("scenario_id"), scenario_id)
        self.assertIn("ml_feature_weight", db_record)

if __name__ == "__main__":
    unittest.main()