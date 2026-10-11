import unittest
from unittest.mock import patch, MagicMock
import json
import io
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
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_load_or_create_storage_success(self):
        random_dict_content = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})

        with patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO(random_dict_content)) as mock_open:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_open.assert_called()

    def test_load_or_create_storage_invalid_data(self):
        invalid_content = json.dumps([uuid.uuid4().hex, random.randint(1, 100)])

        with patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO(invalid_content)) as mock_open:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_open.assert_called()

    def test_pipeline_execute_nominal(self):
        sim_val = round(random.uniform(10.0, 1000.0), 2)
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": sim_val}

        stress_res_list = [round(random.uniform(1.0, 50.0), 2)]
        mock_stress_result = {"symbol": self.symbol, "shifts": self.shifts, "results": stress_res_list}

        impact = random.randint(1, 10)
        mock_report_result = {"symbol": self.symbol, "status": "active", "impact_score": impact}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO("{}")):

            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = mock_sim_result
            sim_instance.run_stress_test.return_value = mock_stress_result

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_report.return_value = mock_report_result

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_report"]["impact_score"], impact)

    def test_pipeline_execute_exceptions_handling(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO("{}")):

            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("Sim fail")
            sim_instance.run_stress_test.side_effect = RuntimeError("Stress fail")

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_report.side_effect = AttributeError("Report fail")

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_nominal(self):
        sim_val = round(random.uniform(5.0, 500.0), 2)
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": sim_val}

        stress_res_list = [round(random.uniform(0.1, 10.0), 2)]

        impact = random.randint(10, 100)
        mock_report_result = {"symbol": self.symbol, "status": "ok", "impact_score": impact}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO("{}")):

            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = mock_sim_result
            sim_instance.run_stress_test.return_value = stress_res_list

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["results"], stress_res_list)
            self.assertEqual(result["stress_report"]["impact_score"], impact)

    def test_run_stress_scenario_pipeline_exceptions(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", side_effect=lambda *args, **kwargs: io.StringIO("invalid_json")):

            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("Key err")
            sim_instance.run_stress_test.side_effect = RuntimeError("Runtime err")

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_reporting.side_effect = AttributeError("Attr err")

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == '__main__':
    unittest.main()