import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_pipeline_execution_success(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        mock_sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": random.uniform(10, 1000)}
        mock_stress_result = [{"shift": s, "result": random.uniform(-100, 100)} for s in shifts]
        mock_report_result = {"symbol": symbol, "status": "stable", "impact_score": random.randint(1, 10)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", create=True) as mock_open:

            mock_file = MagicMock()
            mock_file.read.return_value = "{}"
            mock_open.return_value.__enter__.return_value = mock_file

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.return_value = mock_sim_result
            sim_instance.run_stress_test.return_value = mock_stress_result

            rep_instance = mock_rep_cls.return_value
            rep_instance.run_stress_report.return_value = mock_report_result

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["stress_test"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["symbol"], symbol)

    def test_pipeline_execution_exceptions(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2)]

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", create=True) as mock_open:

            mock_file = MagicMock()
            mock_file.read.side_effect = Exception("Storage error")
            mock_open.return_value.__enter__.return_value = mock_file

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
            sim_instance.run_stress_test.side_effect = RuntimeError("Stress failure")

            rep_instance = mock_rep_cls.return_value
            rep_instance.run_stress_report.side_effect = AttributeError("No attr")

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["percentage"], percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["status"], "default")

    def test_run_stress_scenario_pipeline_function(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2)]

        mock_sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 42.0}
        mock_stress_result = {"symbol": symbol, "shifts": shifts, "results": [1.0]}
        mock_report_result = {"symbol": symbol, "status": "ok", "impact_score": 5}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", create=True) as mock_open:

            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})
            mock_open.return_value.__enter__.return_value = mock_file

            sim_instance = mock_sim_cls.return_value
            sim_instance.simulate_scenario.return_value = mock_sim_result
            sim_instance.run_stress_test.return_value = mock_stress_result

            rep_instance = mock_rep_cls.return_value
            rep_instance.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["stress_test"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["symbol"], symbol)

    def test_storage_validation_non_dict(self):
        storage_file = f"{uuid.uuid4().hex}.json"

        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps([uuid.uuid4().hex, uuid.uuid4().hex])
            mock_open.return_value.__enter__.return_value = mock_file

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            pipeline._load_or_create_storage()

            mock_open.assert_any_call(storage_file, "w", encoding="utf-8")