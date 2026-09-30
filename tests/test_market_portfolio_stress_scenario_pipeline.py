import unittest
from unittest.mock import patch, mock_open
import json
import io
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_class_pipeline_execution(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        expected_sim = {"status": uuid.uuid4().hex}
        expected_test = {"status": uuid.uuid4().hex}
        expected_report = {"status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = expected_sim
            mock_sim_instance.run_stress_test.return_value = expected_test

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = expected_report

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, rand_shifts)

            mock_sim_cls.assert_called_once_with(rand_storage)
            mock_rep_cls.assert_called_once_with(rand_storage)
            mock_sim_instance.simulate_scenario.assert_called_once_with(rand_symbol, rand_percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(rand_symbol, rand_shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(rand_symbol, rand_shifts)

            self.assertEqual(result["simulation"], expected_sim)
            self.assertEqual(result["stress_test"], expected_test)
            self.assertEqual(result["stress_report"], expected_report)

    def test_functional_pipeline_valid_storage(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"TICK_{uuid.uuid4().hex[:6]}"
        rand_percentage = round(random.uniform(0.1, 100.0), 2)
        rand_shifts = [round(random.uniform(-20.0, 20.0), 2)]

        storage_data = {uuid.uuid4().hex: random.randint(1, 100)}
        file_content = json.dumps(storage_data)

        sim_ret = {uuid.uuid4().hex: uuid.uuid4().hex}
        test_ret = [uuid.uuid4().hex]
        report_ret = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_file = mock_open(read_data=file_content)

        with patch("builtins.open", mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_inst = mock_sim_cls.return_value
            mock_sim_inst.simulate_scenario.return_value = sim_ret
            mock_sim_inst.run_stress_test.return_value = test_ret

            mock_rep_inst = mock_rep_cls.return_value
            mock_rep_inst.run_stress_reporting.return_value = report_ret

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            mock_sim_cls.assert_called_with(rand_storage)
            mock_rep_cls.assert_called_with(rand_storage)
            mock_sim_inst.simulate_scenario.assert_called_with(rand_symbol, rand_percentage)
            mock_sim_inst.run_stress_test.assert_called_with(rand_symbol, rand_shifts)
            mock_rep_inst.run_stress_reporting.assert_called_with(rand_symbol, rand_shifts)

            self.assertEqual(result["simulation"], sim_ret)
            self.assertEqual(result["stress_test"]["results"], test_ret)
            self.assertEqual(result["stress_report"], report_ret)

    def test_functional_pipeline_corrupted_storage_and_exceptions(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"FAIL_{uuid.uuid4().hex[:6]}"
        rand_percentage = round(random.uniform(1, 10), 2)
        rand_shifts = [1.0, 2.0]

        mock_file = mock_open(read_data=uuid.uuid4().hex)

        with patch("builtins.open", mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_inst = mock_sim_cls.return_value
            mock_sim_inst.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)
            mock_sim_inst.run_stress_test.side_effect = KeyError(uuid.uuid4().hex)

            mock_rep_inst = mock_rep_cls.return_value
            mock_rep_inst.run_stress_reporting.side_effect = RuntimeError(uuid.uuid4().hex)

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["simulation"]["percentage"], rand_percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_test"]["shifts"], rand_shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()