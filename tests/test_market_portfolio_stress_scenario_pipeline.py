import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string

from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline,
)


class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_pipeline_class_execution_success(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)

        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": 42.0}
        mock_stress_result = {"symbol": self.symbol, "shifts": self.shifts, "results": [1.0, 2.0]}
        mock_report_result = {"symbol": self.symbol, "status": "ok", "impact_score": 100}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="{}"):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_result

            instance_rep = MockRep.return_value
            instance_rep.run_stress_report.return_value = mock_report_result

            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_pipeline_class_execution_fallback(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", side_effect=FileNotFoundError):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("missing")
            instance_sim.run_stress_test.side_effect = KeyError("missing")

            instance_rep = MockRep.return_value
            instance_rep.run_stress_report.side_effect = RuntimeError("error")

            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_function(self):
        mock_sim_result = {"percentage": self.percentage, "simulated_value": 99.9}
        mock_stress_result = [10.0, 20.0]
        mock_report_result = {"status": "warning", "impact_score": 50}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep, \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="invalid json"):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_result

            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [10.0, 20.0])
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "warning")


if __name__ == "__main__":
    unittest.main()