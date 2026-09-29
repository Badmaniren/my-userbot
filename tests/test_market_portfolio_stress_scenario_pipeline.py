import unittest
from unittest.mock import patch, MagicMock
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
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 4))]

    def test_pipeline_class_execution(self):
        sim_data = {"status": uuid.uuid4().hex, "val": random.random()}
        stress_data = [{"shift": s, "val": random.random()} for s in self.shifts]
        report_data = {"impact": uuid.uuid4().hex, "score": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_data
            mock_sim_instance.run_stress_test.return_value = stress_data

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_data

            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            mock_sim_instance.simulate_scenario.assert_called_once_with(self.symbol, self.percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(self.symbol, self.shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(self.symbol, self.shifts)

            self.assertEqual(result["simulation"], sim_data)
            self.assertEqual(result["stress_test"], stress_data)
            self.assertEqual(result["stress_report"], report_data)

    def test_run_stress_scenario_pipeline_valid_storage(self):
        valid_dict = {uuid.uuid4().hex: random.randint(100, 999)}
        storage_content = json.dumps(valid_dict)

        sim_result_data = {"sim": uuid.uuid4().hex}
        stress_list_data = [{"s": random.random()}]
        stress_report_data = {"rep": uuid.uuid4().hex}

        mock_file = io.BytesIO(storage_content.encode("utf-8"))
        mock_file.name = self.storage_file

        with patch("builtins.open", return_value=mock_file) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_result_data
            mock_sim_instance.run_stress_test.return_value = stress_list_data

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = stress_report_data

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(res["simulation"], sim_result_data)
            self.assertEqual(res["stress_test"]["symbol"], self.symbol)
            self.assertEqual(res["stress_test"]["shifts"], self.shifts)
            self.assertEqual(res["stress_test"]["results"], stress_list_data)
            self.assertEqual(res["stress_report"], stress_report_data)

    def test_run_stress_scenario_pipeline_invalid_storage_recovers(self):
        invalid_content = "invalid_json_data_xyz_" + uuid.uuid4().hex
        mock_file = io.BytesIO(invalid_content.encode("utf-8"))
        mock_file.name = self.storage_file

        sim_result_data = {"custom_sim": uuid.uuid4().hex}
        stress_dict_data = {"results": [random.random()]}
        stress_report_data = {"status": uuid.uuid4().hex}

        with patch("builtins.open", return_value=mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_result_data
            mock_sim_instance.run_stress_test.return_value = stress_dict_data

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = stress_report_data

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(res["simulation"], sim_result_data)
            self.assertEqual(res["stress_test"], stress_dict_data)
            self.assertEqual(res["stress_report"], stress_report_data)

    def test_run_stress_scenario_pipeline_exceptions_handling(self):
        mock_file = io.BytesIO(json.dumps({}).encode("utf-8"))
        mock_file.name = self.storage_file

        with patch("builtins.open", return_value=mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = KeyError("Sim error")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Stress error")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.side_effect = Exception("Report error")

            res = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(res["simulation"]["symbol"], self.symbol)
            self.assertEqual(res["simulation"]["percentage"], self.percentage)
            self.assertEqual(res["simulation"]["simulated_value"], 0.0)

            self.assertEqual(res["stress_test"]["symbol"], self.symbol)
            self.assertEqual(res["stress_test"]["shifts"], self.shifts)
            self.assertEqual(res["stress_test"]["results"], [])

            self.assertEqual(res["stress_report"]["symbol"], self.symbol)
            self.assertEqual(res["stress_report"]["status"], "default")
            self.assertEqual(res["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()