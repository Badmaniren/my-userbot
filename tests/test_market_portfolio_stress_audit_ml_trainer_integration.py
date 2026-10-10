import unittest
import uuid
import random
import os
from datetime import datetime

from skills.market_portfolio_stress_audit_ml_trainer import train_portfolio_stress_ml_model
from skills.db_storage import DBStorage
from skills.market_portfolio_collector_agent import collect_portfolio_stress_data
from skills.market_portfolio_stress_scenario_matrix_evaluator import evaluate_stress_scenarios

class TestMarketPortfolioStressAuditMLTrainerIntegration(unittest.TestCase):

    def setUp(self):
        self.db = DBStorage()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.run_id = random.randint(10000, 99999)
        self.test_output_path = f"ml_model_artifacts_{uuid.uuid4().hex[:6]}.pkl"

    def tearDown(self):
        if os.path.exists(self.test_output_path):
            try:
                os.remove(self.test_output_path)
            except OSError:
                pass

    def test_ml_trainer_integration_end_to_end(self):
        historical_data_points = random.randint(50, 200)
        volatility_factor = round(random.uniform(0.1, 3.5), 4)

        raw_data = collect_portfolio_stress_data(
            portfolio_id=self.portfolio_id,
            limit=historical_data_points,
            volatility=volatility_factor
        )

        self.assertIsNotNone(raw_data)

        evaluated_matrix = evaluate_stress_scenarios(
            portfolio_id=self.portfolio_id,
            scenario_seed=self.run_id,
            input_payload=raw_data
        )

        self.assertIn("matrix_id", evaluated_matrix)

        training_result = train_portfolio_stress_ml_model(
            portfolio_id=self.portfolio_id,
            matrix_ref=evaluated_matrix["matrix_id"],
            output_artifact=self.test_output_path,
            epochs=random.randint(5, 15)
        )

        self.assertIsInstance(training_result, dict)
        self.assertEqual(training_result.get("status"), "success")
        self.assertEqual(training_result.get("portfolio_id"), self.portfolio_id)
        self.assertTrue(os.path.exists(self.test_output_path))
        self.assertGreater(os.path.getsize(self.test_output_path), 0)

        persisted_record = self.db.get_ml_audit_model_metadata(training_result.get("model_id"))
        self.assertIsNotNone(persisted_record)
        self.assertEqual(persisted_record["portfolio_id"], self.portfolio_id)

if __name__ == "__main__":
    unittest.main()