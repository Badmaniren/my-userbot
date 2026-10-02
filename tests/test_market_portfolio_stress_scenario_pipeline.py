import unittest
from unittest.mock import patch, mock_open
import io
import json
import random
import uuid
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def test_pipeline_class_execution_success(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]
        rand_sim_val = round(random.uniform(100.0, 1000.0), 2)
        rand_impact = random.randint(1, 100)

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({}))):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"simulated_value": rand_sim_val}
            mock_sim_instance.run_stress_test.return_value = [{"shift": s, "result": s * 2} for s in rand_shifts]

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = {"status": "ok", "impact_score": rand_impact}

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, rand_shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], rand_sim_val)
            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["impact_score"], rand_impact)

    def test_pipeline_class_storage_invalid_json(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-5.0, 5.0), 2)]
        corrupted_data = f"INVALID_JSON_{uuid.uuid4().hex}"

        m_open = mock_open(read_data=corrupted_data)
        with patch("builtins.open", m_open), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_cls.return_value.simulate_scenario.side_effect = KeyError("Missing symbol")
            mock_sim_cls.return_value.run_stress_test.side_effect = KeyError("Missing shifts")
            mock_rep_cls.return_value.run_stress_report.side_effect = RuntimeError("Failed report")

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, rand_shifts)

            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_run_stress_scenario_pipeline_function(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2)]
        rand_sim_val = round(random.uniform(10.0, 500.0), 2)
        rand_impact = random.randint(10, 50)

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls, \
             patch("builtins.open", mock_open(read_data=json.dumps({"initialized": True}))):
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": rand_symbol, "simulated_value": rand_sim_val}
            mock_sim_instance.run_stress_test.return_value = [{"shift": rand_shifts[0], "val": 123}]

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_reporting.return_value = {"symbol": rand_symbol, "impact_score": rand_impact}

            result = run_stress_scenario_pipeline(rand_storage, rand_symbol, rand_percentage, rand_shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], rand_sim_val)
            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["impact_score"], rand_impact)

    def test_pipeline_exceptions_and_fallbacks(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_percentage = round(random.uniform(1.0, 50.0), 2)
        rand_shifts = [round(random.uniform(-10.0, 10.0), 2)]

        with patch("builtins.open", side_effect=FileNotFoundError), \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_cls.return_value.simulate_scenario.return_value = {}
            mock_sim_cls.return_value.run_stress_test.return_value = []

            mock_rep_cls.return_value.run_stress_report.side_effect = AttributeError("No attr")

            pipeline = PortfolioStressScenarioPipeline(rand_storage)
            result = pipeline.execute(rand_symbol, rand_percentage, rand_shifts)

            self.assertEqual(result["simulation"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_test"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], rand_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")

if __name__ == "__main__":
    unittest.main()