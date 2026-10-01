import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 5))]

    def test_pipeline_class_execution_valid_storage(self):
        mock_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        file_content = json.dumps(mock_data)

        sim_val = round(random.uniform(10.0, 500.0), 2)
        stress_res = [round(random.uniform(-5.0, 5.0), 2) for _ in range(3)]
        report_res = {"symbol": self.symbol, "status": ''.join(random.choices(string.ascii_lowercase, k=5)), "impact_score": random.randint(1, 10)}

        with patch("builtins.open", unittest.mock.mock_open(read_data=file_content)) as mock_file:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
                with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                    instance_sim = MockSim.return_value
                    instance_sim.simulate_scenario.return_value = {"simulated_value": sim_val}
                    instance_sim.run_stress_test.return_value = stress_res

                    instance_rep = MockRep.return_value
                    instance_rep.run_stress_report.return_value = report_res

                    pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                    result = pipeline.execute(self.symbol, self.percentage, self.shifts)

                    self.assertIn("simulation", result)
                    self.assertIn("stress_test", result)
                    self.assertIn("stress_report", result)
                    self.assertEqual(result["simulation"]["simulated_value"], sim_val)
                    self.assertEqual(result["stress_test"]["results"], stress_res)
                    self.assertEqual(result["stress_report"], report_res)

    def test_pipeline_class_execution_file_not_found(self):
        sim_val = round(random.uniform(1.0, 100.0), 2)

        with patch("builtins.open", side_effect=FileNotFoundError) as mock_file:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
                with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockRep:
                    instance_sim = MockSim.return_value
                    instance_sim.simulate_scenario.side_effect = KeyError
                    instance_sim.run_stress_test.side_effect = KeyError

                    instance_rep = MockRep.return_value
                    instance_rep.run_stress_report.side_effect = RuntimeError

                    pipeline = PortfolioStressScenarioPipeline(self.storage_file)
                    result = pipeline.execute(self.symbol, self.percentage, self.shifts)

                    self.assertEqual(result["simulation"]["symbol"], self.symbol)
                    self.assertEqual(result["simulation"]["percentage"], self.percentage)
                    self.assertEqual(result["simulation"]["simulated_value"], 0.0)
                    self.assertEqual(result["stress_test"]["results"], [])
                    self.assertEqual(result["stress_report"]["status"], "default")

    def test_pipeline_function_execution_json_decode_error(self):
        invalid_json = uuid.uuid4().hex

        with patch("builtins.open", unittest.mock.mock_open(read_data=invalid_json)) as mock_file:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
                with patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep:
                    instance_sim = MockSim.return_value
                    instance_sim.simulate_scenario.return_value = {"val": random.randint(1, 50)}
                    instance_sim.run_stress_test.return_value = {"res": uuid.uuid4().hex}

                    instance_rep = MockRep.return_value
                    instance_rep.run_stress_reporting.side_effect = AttributeError

                    result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

                    self.assertIn("simulation", result)
                    self.assertIn("stress_test", result)
                    self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_pipeline_function_stress_test_list_conversion(self):
        valid_data = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})
        raw_list_result = [random.randint(1, 10), random.randint(11, 20)]

        with patch("builtins.open", unittest.mock.mock_open(read_data=valid_data)):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSim:
                with patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockRep:
                    instance_sim = MockSim.return_value
                    instance_sim.simulate_scenario.return_value = {"test": self.symbol}
                    instance_sim.run_stress_test.return_value = raw_list_result

                    instance_rep = MockRep.return_value
                    instance_rep.run_stress_reporting.return_value = {"status": "ok"}

                    result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

                    self.assertEqual(result["stress_test"]["symbol"], self.symbol)
                    self.assertEqual(result["stress_test"]["shifts"], self.shifts)
                    self.assertEqual(result["stress_test"]["results"], raw_list_result)


if __name__ == '__main__':
    unittest.main()