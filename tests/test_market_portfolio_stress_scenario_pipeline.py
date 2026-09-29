import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_portfolio_stress_scenario_pipeline_class(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_res = [round(random.uniform(10.0, 50.0), 2) for _ in range(3)]
        report_res = {"status": uuid.uuid4().hex, "impact": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_res

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, rand_shifts)

            mock_sim_cls.assert_called_once_with(rand_storage)
            mock_rep_cls.assert_called_once_with(rand_storage)
            mock_sim_instance.simulate_scenario.assert_called_once_with(rand_symbol, rand_percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(rand_symbol, rand_shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(rand_symbol, rand_shifts)

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"], stress_res)
            self.assertEqual(result["stress_report"], report_res)

    def test_portfolio_stress_scenario_pipeline_int_shifts_normalization(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        int_shifts = 3
        expected_shifts_iter = [0, 1, 2]

        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_res = [round(random.uniform(10.0, 50.0), 2) for _ in range(3)]
        report_res = {"status": uuid.uuid4().hex, "impact": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_res

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, int_shifts)

            mock_sim_instance.run_stress_test.assert_called_once_with(rand_symbol, expected_shifts_iter)
            mock_rep_instance.run_stress_report.assert_called_once_with(rand_symbol, expected_shifts_iter)

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"], stress_res)

    def test_run_stress_scenario_pipeline_success(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(2)]

        valid_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        file_content = json.dumps(valid_dict)

        sim_val = {"symbol": rand_symbol, "val": round(random.uniform(10.0, 100.0), 2)}
        stress_res = [round(random.uniform(1.0, 10.0), 2)]
        report_res = {"symbol": rand_symbol, "score": random.randint(10, 50)}

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = stress_res

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_res

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            mock_sim_instance.simulate_scenario.assert_called_once_with(rand_symbol, rand_percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(rand_symbol, rand_shifts)
            mock_rep_instance.run_stress_reporting.assert_called_once_with(rand_symbol, rand_shifts)

            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_test"]["results"], stress_res)
            self.assertEqual(result["stress_report"], report_res)

    def test_run_stress_scenario_pipeline_storage_error_recovery(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = []

        corrupted_data = uuid.uuid4().hex

        with patch("builtins.open", mock_open(read_data=corrupted_data)) as mock_file, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError(rand_symbol)
            mock_sim_instance.run_stress_test.side_effect = KeyError(rand_symbol)

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception(uuid.uuid4().hex)

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            mock_file.assert_any_call(rand_storage, "w", encoding="utf-8")

            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["simulation"]["percentage"], rand_percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_test"]["shifts"], rand_shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_stress_test_list_conversion(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(1.0, 10.0), 2)]

        valid_dict = {}
        file_content = json.dumps(valid_dict)
        sim_val = uuid.uuid4().hex
        raw_list_result = [uuid.uuid4().hex, random.randint(1, 100)]
        report_res = uuid.uuid4().hex

        with patch("builtins.open", mock_open(read_data=file_content)), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_val
            mock_sim_instance.run_stress_test.return_value = raw_list_result

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_res

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            expected_stress_test_dict = {
                "symbol": rand_symbol,
                "shifts": rand_shifts,
                "results": raw_list_result
            }

            self.assertEqual(result["stress_test"], expected_stress_test_dict)
            self.assertEqual(result["simulation"], sim_val)
            self.assertEqual(result["stress_report"], report_res)

if __name__ == "__main__":
    unittest.main()