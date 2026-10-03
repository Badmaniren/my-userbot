import unittest
from unittest.mock import patch, mock_open
import json
import io
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def test_pipeline_class_execution_success(self):
        storage_file_path = f"{uuid.uuid4().hex}.json"
        symbol_name = f"SYM_{uuid.uuid4().hex[:6]}"
        pct_value = round(random.uniform(-50.0, 50.0), 2)
        shift_list = [random.randint(-10, 10), random.randint(-20, 20)]

        initial_storage_data = json.dumps({"status": "active", "id": uuid.uuid4().hex})

        sim_output = {"simulated_value": round(random.uniform(10.0, 100.0), 2)}
        stress_test_output = [{"shift": s, "result": round(random.uniform(-5.0, 5.0), 2)} for s in shift_list]
        stress_report_output = {"status": "ok", "impact_score": random.randint(1, 100)}

        with patch("builtins.open", mock_open(read_data=initial_storage_data)) as mocked_file:
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:

                instance_sim = MockSimulator.return_value
                instance_sim.simulate_scenario.return_value = sim_output
                instance_sim.run_stress_test.return_value = stress_test_output

                instance_rep = MockReporter.return_value
                instance_rep.run_stress_report.return_value = stress_report_output

                pipeline_instance = PortfolioStressScenarioPipeline(storage_file_path)
                result = pipeline_instance.execute(symbol_name, pct_value, shift_list)

                self.assertIsInstance(result, dict)
                self.assertIn("simulation", result)
                self.assertIn("stress_test", result)
                self.assertIn("stress_report", result)

                self.assertEqual(result["simulation"]["symbol"], symbol_name)
                self.assertEqual(result["simulation"]["simulated_value"], sim_output["simulated_value"])

                self.assertEqual(result["stress_test"]["symbol"], symbol_name)
                self.assertEqual(result["stress_test"]["shifts"], shift_list)
                self.assertEqual(result["stress_test"]["results"], stress_test_output)

                self.assertEqual(result["stress_report"]["symbol"], symbol_name)
                self.assertEqual(result["stress_report"]["impact_score"], stress_report_output["impact_score"])

    def test_pipeline_class_execution_exceptions_and_fallbacks(self):
        storage_file_path = f"{uuid.uuid4().hex}.json"
        symbol_name = f"SYM_{uuid.uuid4().hex[:6]}"
        pct_value = round(random.uniform(-50.0, 50.0), 2)
        shift_list = [random.randint(-5, 5)]

        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:

                instance_sim = MockSimulator.return_value
                instance_sim.simulate_scenario.side_effect = KeyError("Missing symbol")
                instance_sim.run_stress_test.side_effect = KeyError("Missing shifts")

                instance_rep = MockReporter.return_value
                instance_rep.run_stress_report.side_effect = RuntimeError("System fault")

                pipeline_instance = PortfolioStressScenarioPipeline(storage_file_path)
                result = pipeline_instance.execute(symbol_name, pct_value, shift_list)

                self.assertIsInstance(result, dict)
                self.assertEqual(result["simulation"]["symbol"], symbol_name)
                self.assertEqual(result["simulation"]["percentage"], pct_value)
                self.assertEqual(result["simulation"]["simulated_value"], 0.0)

                self.assertEqual(result["stress_test"]["symbol"], symbol_name)
                self.assertEqual(result["stress_test"]["shifts"], shift_list)
                self.assertEqual(result["stress_test"]["results"], [])

                self.assertEqual(result["stress_report"]["symbol"], symbol_name)
                self.assertEqual(result["stress_report"]["status"], "default")
                self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_functional(self):
        storage_file_path = f"{uuid.uuid4().hex}.json"
        symbol_name = f"SYM_{uuid.uuid4().hex[:6]}"
        pct_value = round(random.uniform(-100.0, 100.0), 2)
        shift_list = [random.randint(-15, 15)]

        corrupted_content = f"INVALID_JSON_{uuid.uuid4().hex}"
        sim_output_dict = {"symbol": symbol_name, "custom_metric": uuid.uuid4().hex}
        stress_test_list = [{"shift_id": random.randint(1, 10)}]
        reporter_output = {"status": "warning", "impact_score": 99}

        with patch("builtins.open", mock_open(read_data=corrupted_content)):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter:

                instance_sim = MockSimulator.return_value
                instance_sim.simulate_scenario.return_value = sim_output_dict
                instance_sim.run_stress_test.return_value = stress_test_list

                instance_rep = MockReporter.return_value
                instance_rep.run_stress_reporting.return_value = reporter_output

                result = run_stress_scenario_pipeline(storage_file_path, symbol_name, pct_value, shift_list)

                self.assertIsInstance(result, dict)
                self.assertEqual(result["simulation"]["symbol"], symbol_name)
                self.assertEqual(result["simulation"]["custom_metric"], sim_output_dict["custom_metric"])

                self.assertEqual(result["stress_test"]["symbol"], symbol_name)
                self.assertEqual(result["stress_test"]["shifts"], shift_list)
                self.assertEqual(result["stress_test"]["results"], stress_test_list)

                self.assertEqual(result["stress_report"]["symbol"], symbol_name)
                self.assertEqual(result["stress_report"]["status"], "warning")
                self.assertEqual(result["stress_report"]["impact_score"], 99)

    def test_pipeline_file_write_recovery_on_invalid_data(self):
        storage_file_path = f"{uuid.uuid4().hex}.json"
        symbol_name = f"SYM_{uuid.uuid4().hex[:6]}"
        pct_value = round(random.uniform(-10.0, 10.0), 2)
        shift_list = []

        mocked_file_handle = mock_open(read_data='["not_a_dict"]')
        
        with patch("builtins.open", mocked_file_handle):
            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:

                instance_sim = MockSimulator.return_value
                instance_sim.simulate_scenario.return_value = {}
                instance_sim.run_stress_test.return_value = {}

                instance_rep = MockReporter.return_value
                instance_rep.run_stress_report.return_value = {}

                pipeline_instance = PortfolioStressScenarioPipeline(storage_file_path)
                result = pipeline_instance.execute(symbol_name, pct_value, shift_list)

                self.assertIsInstance(result, dict)
                mocked_file_handle().write.assert_any_call("{}")

if __name__ == "__main__":
    unittest.main()