import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import (
    PortfolioStressScenarioPipeline,
    run_stress_scenario_pipeline
)

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def test_pipeline_class_initialization_and_execution_success(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

        sim_output = {"symbol": symbol, "percentage": percentage, "simulated_value": round(random.uniform(100, 1000), 2)}
        stress_output = [{"shift": s, "impact": round(random.uniform(-50, 50), 2)} for s in shifts]
        report_output = {"symbol": symbol, "status": "active", "impact_score": random.randint(1, 10)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({"initialized": True}))) as mock_file:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_output
            mock_sim_instance.run_stress_test.return_value = stress_output

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = report_output

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            mock_sim_instance.simulate_scenario.assert_called_once_with(symbol, percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(symbol, shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(symbol, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["percentage"], percentage)
            self.assertEqual(result["stress_test"]["results"], stress_output)
            self.assertEqual(result["stress_report"]["status"], "active")

    def test_pipeline_class_fallback_on_exceptions(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"TICK_{uuid.uuid4().hex[:6]}"
        percentage = round(random.uniform(0.1, 10.0), 2)
        shifts = [round(random.uniform(-0.05, 0.05), 4)]

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", side_effect=FileNotFoundError):

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.side_effect = RuntimeError("Sim fail")
            mock_sim_instance.run_stress_test.side_effect = KeyError("Test fail")

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.side_effect = AttributeError("Report fail")

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["percentage"], percentage)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)

            self.assertEqual(result["stress_test"]["symbol"], symbol)
            self.assertEqual(result["stress_test"]["shifts"], shifts)
            self.assertEqual(result["stress_test"]["results"], [])

            self.assertEqual(result["stress_report"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_functional_success(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"ASSET_{uuid.uuid4().hex[:6]}"
        percentage = round(random.uniform(5.0, 25.0), 2)
        shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(2)]

        sim_output = {"symbol": symbol, "simulated_value": 450.5}
        stress_output = {"results": [{"shift": 0.1, "val": 10}]}
        report_output = {"status": "ok", "impact_score": 5}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({"test": 123}))) as mock_file:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = sim_output
            mock_sim_instance.run_stress_test.return_value = stress_output

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = report_output

            result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["percentage"], percentage)
            self.assertEqual(result["stress_test"]["results"], stress_output["results"])
            self.assertEqual(result["stress_report"]["status"], "ok")

    def test_run_stress_scenario_pipeline_storage_corruption_recovery(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"CORRUPT_{uuid.uuid4().hex[:6]}"
        percentage = 15.0
        shifts = [0.01]

        corrupted_data = "Not a JSON dictionary"

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=corrupted_data)) as mock_file:

            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": symbol}
            mock_sim_instance.run_stress_test.return_value = []

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"status": "error"}

            result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            mock_file.assert_any_call(storage_file, "w", encoding="utf-8")

if __name__ == "__main__":
    unittest.main()