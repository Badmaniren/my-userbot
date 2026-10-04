import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = [round(random.uniform(-15.0, -1.0), 2), round(random.uniform(1.0, 15.0), 2)]

    def test_pipeline_execute_success(self):
        sim_val = round(random.uniform(50.0, 500.0), 2)
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": sim_val}
        mock_stress_result = [{"shift_percentage": self.shifts[0], "resulting_valuation": 10.0}]
        mock_report_result = {"symbol": self.symbol, "status": "active", "impact_score": 42}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data='{}')):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_result

            instance_rep = MockRep.return_value
            instance_rep.run_stress_report.return_value = mock_report_result

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], 42)

    def test_pipeline_execute_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data='invalid_json')):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Sim error")
            instance_sim.run_stress_test.side_effect = KeyError("Stress error")

            instance_rep = MockRep.return_value
            instance_rep.run_stress_report.side_effect = RuntimeError("Report error")

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_run_stress_scenario_pipeline_success(self):
        sim_val = round(random.uniform(10.0, 100.0), 2)
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": sim_val}
        mock_stress_result = {"symbol": self.symbol, "shifts": self.shifts, "results": [{"shift": 1, "val": 5.0}]}
        mock_report_result = {"symbol": self.symbol, "status": "ok", "impact_score": 100}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data='{}')):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.return_value = mock_sim_result
            instance_sim.run_stress_test.return_value = mock_stress_result

            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "ok")

    def test_run_stress_scenario_pipeline_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data='{"not": "a_dict_or_bad"}')):

            instance_sim = MockSim.return_value
            instance_sim.simulate_scenario.side_effect = KeyError("Sim fail")
            instance_sim.run_stress_test.side_effect = KeyError("Test fail")

            instance_rep = MockRep.return_value
            instance_rep.run_stress_reporting.side_effect = AttributeError("Report fail")

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_load_or_create_storage_invalid_data(self):
        with patch("builtins.open", mock_open(read_data='[]')) as mock_file:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_file.assert_any_call(self.storage_file, "w", encoding="utf-8")

if __name__ == "__main__":
    unittest.main()