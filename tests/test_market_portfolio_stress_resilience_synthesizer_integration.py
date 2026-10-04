import unittest
import uuid
import os
import random
import tempfile
from skills.market_portfolio_stress_resilience_synthesizer import (
    MarketPortfolioStressResilienceSynthesizer,
    market_portfolio_stress_resilience_synthesizer
)

class RealEngineAdapter:
    def calculate_var(self, portfolio_id: str) -> dict:
        val = random.uniform(50.0, 500.0)
        return {"var_95": val}

class RealSimulatorAdapter:
    def run_simulation(self, portfolio_id: str) -> dict:
        dd = random.uniform(0.05, 0.5)
        return {"max_drawdown": dd, "impact": dd * 1.5}

class RealRecoveryAdapter:
    def estimate_recovery_time(self, portfolio_id: str) -> dict:
        days = random.randint(10, 120)
        return {"recovery_days": days}

class RealDBStorageAdapter:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.saved_data = {}

    def save(self, portfolio_id: str, data: dict) -> None:
        self.saved_data[portfolio_id] = data

class TestMarketPortfolioStressResilienceSynthesizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.simulation_run_id = str(uuid.uuid4())

        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, f"test_db_{uuid.uuid4()}.db")

        self.monte_carlo = RealEngineAdapter()
        self.simulator = RealSimulatorAdapter()
        self.recovery = RealRecoveryAdapter()
        self.db_storage = RealDBStorageAdapter(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_synthesizer_class_integration(self):
        synthesizer = MarketPortfolioStressResilienceSynthesizer(
            db_storage=self.db_storage,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo,
            market_portfolio_scenario_simulator=self.simulator,
            market_portfolio_stress_recovery_coordinator_bridge=self.recovery
        )

        result = synthesizer.synthesize(self.portfolio_id)

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("resilience_index", result)
        self.assertIsInstance(result["resilience_index"], float)
        self.assertIn("components", result)
        self.assertIn("var", result["components"])
        self.assertIn("max_drawdown", result["components"])
        self.assertIn("recovery_days", result["components"])

        self.assertIn(self.portfolio_id, self.db_storage.saved_data)
        saved_record = self.db_storage.saved_data[self.portfolio_id]
        self.assertEqual(saved_record["portfolio_id"], self.portfolio_id)
        self.assertEqual(saved_record["resilience_index"], result["resilience_index"])

    def test_synthesizer_function_integration(self):
        input_payload = {
            "portfolio_id": self.portfolio_id,
            "simulation_run_id": self.simulation_run_id,
            "db_storage": f"sqlite:///{self.db_path}"
        }

        result = market_portfolio_stress_resilience_synthesizer(input_payload)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["simulation_run_id"], self.simulation_run_id)
        self.assertIn("artifact_path", result)

        artifact_path = result["artifact_path"]
        self.assertTrue(os.path.exists(artifact_path))

        with open(artifact_path, "r", encoding="utf-8") as f:
            artifact_content = f.read()
            self.assertTrue(len(artifact_content) > 0)

    def test_invalid_portfolio_id_handling(self):
        synthesizer = MarketPortfolioStressResilienceSynthesizer()
        invalid_id = f"not-a-uuid-{random.randint(1000, 9999)}"

        result = synthesizer.synthesize(invalid_id)
        self.assertIn("error", result)
        self.assertEqual(result["resilience_index"], 0.0)
        self.assertEqual(result["portfolio_id"], invalid_id)

if __name__ == "__main__":
    unittest.main()