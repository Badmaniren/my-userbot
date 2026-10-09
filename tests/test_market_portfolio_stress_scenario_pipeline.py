import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json

from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)


class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_load_or_create_storage_failure_creates_file(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:6].upper()
        rand_pct = random.uniform(1.0, 50.0)
        rand_shifts = [random.randint(-10, 10), random.randint(-20, 20)]

        mock_file_instance = mock_open().return_value

        with patch("builtins.open", side_effect=[FileNotFoundError, mock_file_instance]) as mocked_file:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                
                mock_sim_instance = MockSim.return_value
                mock_sim_instance.simulate_scenario.return_value = {"symbol": rand_symbol, "percentage": rand_pct, "simulated_value": 42.0}
                mock_sim_instance.run_stress_test.return_value = {"symbol": rand_symbol, "shifts": rand_shifts, "results": [1, 2, 3]}

                mock_rep_instance = MockRep.return_value
                mock_rep_instance.run_stress_report.return_value = {"symbol": rand_symbol, "status": "ok", "impact_score": 5}

                pipeline = PortfolioStressScenarioPipeline(rand_storage)
                res = pipeline.execute(rand_symbol, rand_pct, rand_shifts)

                self.assertIn("simulation", res)
                self.assertIn("stress_test", res)
                self.assertIn("stress_report", res)
                self.assertEqual(res["simulation"]["symbol"], rand_symbol)

    def test_pipeline_execution_success(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_pct = round(random.uniform(5.0, 25.0), 2)
        rand_shifts = [random.randint(-5, 5)]

        valid_data_bytes = io.BytesIO(json.dumps({uuid.uuid4().hex: random.randint(1, 100)}).encode("utf-8"))

        with patch("builtins.open", return_value=valid_data_bytes):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                
                sim_data = {"symbol": rand_symbol, "percentage": rand_pct, "simulated_value": 123.45}
                test_data = {"symbol": rand_symbol, "shifts": rand_shifts, "results": [99]}
                rep_data = {"symbol": rand_symbol, "status": "active", "impact_score": 10}

                MockSim.return_value.simulate_scenario.return_value = sim_data
                MockSim.return_value.run_stress_test.return_value = test_data
                MockRep.return_value.run_stress_report.return_value = rep_data

                pipeline = PortfolioStressScenarioPipeline(rand_storage)
                result = pipeline.execute(rand_symbol, rand_pct, rand_shifts)

                self.assertEqual(result["simulation"]["simulated_value"], 123.45)
                self.assertEqual(result["stress_test"]["results"], [99])
                self.assertEqual(result["stress_report"]["impact_score"], 10)

    def function_wrapper_execution_test(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex[:4].upper()
        rand_pct = random.uniform(1.0, 10.0)
        rand_shifts = [random.randint(-2, 2)]

        invalid_data_bytes = io.BytesIO(b"corrupted_json_payload")

        with patch("builtins.open", return_value=invalid_data_bytes):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep:
                
                MockSim.return_value.simulate_scenario.side_effect = KeyError("Missing key")
                MockSim.return_value.run_stress_test.side_effect = RuntimeError("Failed test")
                MockRep.return_value.run_stress_reporting.side_effect = AttributeError("No attr")

                res = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_pct, rand_shifts)

                self.assertIn("simulation", res)
                self.assertEqual(res["simulation"]["symbol"], rand_symbol)
                self.assertEqual(res["simulation"]["percentage"], rand_pct)
                self.assertEqual(res["simulation"]["simulated_value"], 0.0)
                self.assertEqual(res["stress_test"]["results"], [])
                self.assertEqual(res["stress_report"]["status"], "default")


if __name__ == "__main__":
    unittest.main()