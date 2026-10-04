import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def test_load_or_create_storage_valid(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        file_content = json.dumps({random_key: random_val})

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = file_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            pipeline._load_or_create_storage()
            mock_open.assert_called_with(self.storage_file, "r", encoding="utf-8", errors="ignore")

    def test_load_or_create_storage_invalid(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        invalid_content = uuid.uuid4().hex

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = invalid_content
            mock_open.return_value.__enter__.return_value = mock_file
            
            pipeline._load_or_create_storage()
            mock_open.assert_any_call(self.storage_file, "w", encoding="utf-8")

    def test_pipeline_execute_success(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_res = [{"shift": s, "impact": round(random.uniform(-5.0, 5.0), 2)} for s in self.shifts]
        report_score = random.randint(1, 100)

        with patch.object(pipeline, "_load_or_create_storage") as mock_load, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = {"simulated_value": sim_val}
            sim_instance.run_stress_test.return_value = stress_res

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_report.return_value = {"impact_score": report_score}

            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            mock_load.assert_called_once()
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], stress_res)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["impact_score"], report_score)

    def test_pipeline_execute_exceptions(self):
        pipeline = PortfolioStressScenarioPipeline(self.storage_file)

        with patch.object(pipeline, "_load_or_create_storage"), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter:
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("sim_error")
            sim_instance.run_stress_test.side_effect = KeyError("test_error")

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_report.side_effect = RuntimeError("report_error")

            result = pipeline.execute(self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_functional(self):
        sim_val = round(random.uniform(50.0, 500.0), 2)
        stress_res_list = [round(random.uniform(-1.0, 1.0), 2) for _ in self.shifts]
        report_status = uuid.uuid4().hex

        with patch("builtins.open", create=True) as mock_open, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter:
            
            mock_file = MagicMock()
            mock_file.read.return_value = "{}"
            mock_open.return_value.__enter__.return_value = mock_file

            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = {"simulated_value": sim_val}
            sim_instance.run_stress_test.return_value = stress_res_list

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_reporting.return_value = {"status": report_status}

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertEqual(result["stress_test"]["results"], stress_res_list)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], report_status)