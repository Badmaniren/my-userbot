import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import string

from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def test_pipeline_class_execution_success(self):
        sim_val = round(random.uniform(10.0, 1000.0), 2)
        stress_results = [{"shift": s, "val": round(random.uniform(1.0, 10.0), 2)} for s in self.shifts]
        report_score = random.randint(1, 100)
        report_status = uuid.uuid4().hex[:8]

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data=json.dumps({"initialized": True}))):

            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.return_value = {"value": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_results

            mock_rep_instance = MockRep.return_value
            mock_rep_instance.run_stress_report.return_value = {"impact_score": report_score, "status": report_status}

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["value"], sim_val)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], stress_results)

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], report_score)
            self.assertEqual(result["stress_report"]["status"], report_status)

    def test_pipeline_class_execution_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep, \
             patch("builtins.open", side_effect=FileNotFoundError):

            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("sim_error")
            mock_sim_instance.run_stress_test.side_effect = KeyError("test_error")

            mock_rep_instance = MockRep.return_value
            mock_rep_instance.run_stress_report.side_effect = RuntimeError("report_error")

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_function_success(self):
        sim_val = round(random.uniform(5.0, 500.0), 2)
        stress_results_list = [round(random.uniform(-5.0, 5.0), 2) for _ in self.shifts]
        report_score = random.randint(10, 500)

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data=json.dumps({uuid.uuid4().hex: random.randint(1, 100)}))):

            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.return_value = {"simulated_output": sim_val}
            mock_sim_instance.run_stress_test.return_value = stress_results_list

            mock_rep_instance = MockRep.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"impact_score": report_score}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_output"], sim_val)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], stress_results_list)

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], report_score)

    def test_run_stress_scenario_pipeline_invalid_json(self):
        bad_content = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep, \
             patch("builtins.open", mock_open(read_data=bad_content)):

            mock_sim_instance = MockSim.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": self.symbol, "ok": True}
            mock_sim_instance.run_stress_test.return_value = {"symbol": self.symbol, "results": []}

            mock_rep_instance = MockRep.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"symbol": self.symbol, "status": "ok"}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_io_stream_chaos_reading(self):
        random_bytes = uuid.uuid4().bytes
        mock_file = mock_open(read_data=random_bytes.decode('latin1', errors='ignore'))

        with patch("builtins.open", mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep:

            MockSim.return_value. simulate_scenario.side_effect = KeyError
            MockSim.return_value.run_stress_test.side_effect = KeyError
            MockRep.return_value.run_stress_reporting.side_effect = AttributeError

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(res["simulation"]["symbol"], self.symbol)
            self.assertEqual(res["simulation"]["simulated_value"], 0.0)
            self.assertEqual(res["stress_test"]["results"], [])
            self.assertEqual(res["stress_report"]["status"], "default")

if __name__ == '__main__':
    unittest.main()