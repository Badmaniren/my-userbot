import unittest
import tempfile
import os
import json
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.random_filename = f"{uuid.uuid4().hex}.json"
        self.storage_file = os.path.join(self.temp_dir.name, self.random_filename)
        
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_percentage = round(random.uniform(-50.0, 50.0), 2)
        self.test_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_class_execution(self):
        sim_mock_result = {
            "symbol": self.test_symbol,
            "percentage": self.test_percentage,
            "val": random.randint(100, 1000)
        }
        stress_test_mock_result = {
            "symbol": self.test_symbol,
            "shifts": self.test_shifts,
            "outcome": uuid.uuid4().hex
        }
        stress_report_mock_result = {
            "symbol": self.test_symbol,
            "report_id": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_class, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_class:

            mock_sim_instance = mock_sim_class.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_mock_result
            mock_sim_instance.run_stress_test.return_value = stress_test_mock_result

            mock_rep_instance = mock_rep_class.return_value
            mock_rep_instance.run_stress_report.return_value = stress_report_mock_result

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.test_symbol, self.test_percentage, self.test_shifts)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.test_symbol, self.test_percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(self.test_symbol, self.test_shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(self.test_symbol, self.test_shifts)

            self.assertEqual(result["simulation"], sim_mock_result)
            self.assertEqual(result["stress_test"], stress_test_mock_result)
            self.assertEqual(result["stress_report"], stress_report_mock_result)

    def test_functional_pipeline_valid_storage(self):
        initial_data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        sim_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        stress_val = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_val = {uuid.uuid4().hex: random.random()}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_class, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_class:

            mock_sim = mock_sim_class.return_value
            mock_sim.simulate_scenario.return_value = sim_val
            mock_sim.run_stress_test.return_value = stress_val

            mock_rep = mock_rep_class.return_value
            mock_rep.run_stress_reporting.return_value = report_val

            result = run_stress_scenario_pipeline(
                self.storage_file,
                self.test_symbol,
                self.test_percentage,
                self.test_shifts
            )

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.test_symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.test_shifts)
            self.assertEqual(result["stress_test"]["results"], stress_val)
            self.assertEqual(result["stress_report"], report_val)

    def test_functional_pipeline_corrupted_storage(self):
        garbage_content = uuid.uuid4().bytes + uuid.uuid4().bytes
        
        with patch("builtins.open", side_effect=lambda *args, **kwargs: io.BytesIO(garbage_content) if "r" in args[1] else open(*args, **kwargs)):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_class, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_class:

                mock_sim = mock_sim_class.return_value
                mock_sim.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)
                mock_sim.run_stress_test.side_effect = KeyError(uuid.uuid4().hex)

                mock_rep = mock_rep_class.return_value
                mock_rep.run_stress_reporting.side_effect = Exception(uuid.uuid4().hex)

                result = run_stress_scenario_pipeline(
                    self.storage_file,
                    self.test_symbol,
                    self.test_percentage,
                    self.test_shifts
                )

                self.assertEqual(result["simulation"]["symbol"], self.test_symbol)
                self.assertEqual(result["simulation"]["percentage"], self.test_percentage)
                self.assertEqual(result["simulation"]["simulated_value"], 0.0)

                self.assertEqual(result["stress_test"]["symbol"], self.test_symbol)
                self.assertEqual(result["stress_test"]["shifts"], self.test_shifts)
                self.assertEqual(result["stress_test"]["results"], [])

                self.assertEqual(result["stress_report"]["symbol"], self.test_symbol)
                self.assertEqual(result["stress_report"]["status"], "default")
                self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()