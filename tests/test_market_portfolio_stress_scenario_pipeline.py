import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def test_pipeline_execution_class_success(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        
        sim_val = round(random.uniform(100.0, 1000.0), 2)
        stress_results = [{"shift": s, "val": sim_val * (1 + s/100)} for s in shifts]
        report_score = random.randint(1, 100)

        file_content = json.dumps({uuid.uuid4().hex: random.randint(1, 10)})
        mock_file = MagicMock()
        mock_file.__enter__.return_value = io.StringIO(file_content)

        with patch("builtins.open", return_value=mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_simulator = mock_sim_cls.return_value
            mock_simulator.simulate_scenario.return_value = {"simulated_value": sim_val}
            mock_simulator.run_stress_test.return_value = stress_results

            mock_reporter = mock_rep_cls.return_value
            mock_reporter.run_stress_report.return_value = {"status": "ok", "impact_score": report_score}

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], symbol)
            self.assertEqual(result["stress_test"]["results"], stress_results)
            self.assertEqual(result["stress_report"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["impact_score"], report_score)

    def test_pipeline_execution_class_fallbacks(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2)]

        with patch("builtins.open", side_effect=FileNotFoundError), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_simulator = mock_sim_cls.return_value
            mock_simulator.simulate_scenario.side_effect = KeyError("missing")
            mock_simulator.run_stress_test.side_effect = KeyError("missing")

            mock_reporter = mock_rep_cls.return_value
            mock_reporter.run_stress_report.side_effect = RuntimeError("error")

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["symbol"], symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_function(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2)]
        
        sim_val = round(random.uniform(500.0, 2000.0), 2)

        file_content = json.dumps({uuid.uuid4().hex: random.randint(10, 50)})
        mock_file = MagicMock()
        mock_file.__enter__.return_value = io.StringIO(file_content)

        with patch("builtins.open", return_value=mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:
            
            mock_simulator = mock_sim_cls.return_value
            mock_simulator.simulate_scenario.return_value = {"symbol": symbol, "simulated_value": sim_val}
            mock_simulator.run_stress_test.return_value = [{"shift": shifts[0], "val": sim_val}]

            mock_reporter = mock_rep_cls.return_value
            mock_reporter.run_stress_reporting.return_value = {"symbol": symbol, "status": "active", "impact_score": 99}

            result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_report"]["impact_score"], 99)

    def test_run_stress_scenario_pipeline_invalid_json(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = []

        invalid_content = f"INVALID_JSON_{uuid.uuid4().hex}"
        mock_file = MagicMock()
        mock_file.__enter__.return_value = io.StringIO(invalid_content)

        with patch("builtins.open", return_value=mock_file), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:
            
            mock_simulator = mock_sim_cls.return_value
            mock_simulator.simulate_scenario.return_value = {"simulated_value": 111.1}
            mock_simulator.run_stress_test.return_value = []

            mock_reporter = mock_rep_cls.return_value
            mock_reporter.run_stress_reporting.return_value = {"impact_score": 10}

            result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)
            self.assertEqual(result["simulation"]["symbol"], symbol)
            self.assertEqual(result["stress_report"]["symbol"], symbol)

if __name__ == "__main__":
    unittest.main()