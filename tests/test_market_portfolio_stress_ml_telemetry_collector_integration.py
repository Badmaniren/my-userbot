import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_telemetry_collector import (
    market_portfolio_stress_ml_telemetry_collector,
    start_new
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressMlTelemetryCollectorIntegration(unittest.TestCase):
    def test_telemetry_collector_end_to_end_integration(self):
        unique_telemetry_id = f"tel-{uuid.uuid4()}"
        unique_portfolio_id = f"port-{uuid.uuid4()}"
        unique_scenario_id = f"scen-{uuid.uuid4()}"
        
        matrix_val = round(random.uniform(10.0, 100.0), 4)
        var_val = round(random.uniform(1.0, 50.0), 4)
        weight_val = round(random.uniform(0.1, 1.0), 4)

        payload = {
            "telemetry_id": unique_telemetry_id,
            "portfolio_id": unique_portfolio_id,
            "scenario_id": unique_scenario_id,
            "matrix_metrics": {"stress_score": matrix_val},
            "var_liquidity_metrics": {"var_95": var_val},
            "ml_feature_weight": weight_val
        }

        result = market_portfolio_stress_ml_telemetry_collector(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("telemetry_id"), unique_telemetry_id)
        self.assertEqual(result.get("portfolio_id"), unique_portfolio_id)
        self.assertEqual(result.get("scenario_id"), unique_scenario_id)
        self.assertEqual(result.get("matrix_metrics"), {"stress_score": matrix_val})
        self.assertEqual(result.get("var_liquidity_metrics"), {"var_95": var_val})
        self.assertEqual(result.get("ml_feature_weight"), weight_val)

        stored_record = db_storage({
            "query_type": "get_telemetry",
            "telemetry_id": unique_telemetry_id
        })

        if stored_record:
            self.assertEqual(stored_record.get("telemetry_id"), unique_telemetry_id)
            self.assertEqual(stored_record.get("portfolio_id"), unique_portfolio_id)

        dependencies = {}
        start_result = start_new(dependencies, unique_portfolio_id)
        
        self.assertIsInstance(start_result, dict)
        self.assertEqual(start_result.get("status"), "ok")
        self.assertEqual(start_result.get("portfolio_id"), unique_portfolio_id)

if __name__ == "__main__":
    unittest.main()