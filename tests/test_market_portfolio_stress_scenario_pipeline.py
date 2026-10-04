import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(1, 3))]

    def test_load_or_create_storage_success(self):
        random_content = json.dumps({uuid.uuid4().hex: random.randint(100, 999)})
        mock_file = MagicMock(spec=io.TextIOWrapper)
        mock_file.read.return_value = random_content

        with patch("builtins.open", return_value=mock_file) as mock_open:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_open.assert_called()

    def test_load_or_create_storage_corrupted(self):
        bad_content = "".join(random.choices(string.ascii_letters, k=10))
        mock_file = MagicMock(spec=io.TextIOWrapper)
        mock_file.read.return_value = bad_content

        with patch("builtins.open", return_value=mock_file) as mock_open:
            pipeline = PortfolioStressScenarioPipeline(self.storage_file)
            pipeline._load_or_create_storage()
            mock_open.assert_called()

    def test_pipeline_execute_nominal_flow(self):
        mock_sim_result = {"symbol": self.symbol, "percentage": self.percentage, "simulated_value": random.uniform(10, 1000)}
        mock_stress_result = [{"shift": s, "impact": random.uniform(-5, 5)} for s in self.shifts]
        mock_report_result = {"symbol": self.symbol, "status": "stable", "impact_score": random.randint(1, 100)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="{}"):
            
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
            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)

    def test_pipeline_execute_key_error_handling(self):
        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as MockReporter, \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="{}"):
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.side_effect = KeyError("Missing symbol")
            sim_instance.run_stress_test.side_effect = KeyError("Missing shifts")

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_report.side_effect = RuntimeError("Engine failure")

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

    def test_run_stress_scenario_pipeline_functional_flow(self):
        mock_sim_result = {"simulated_value": random.uniform(50, 500)}
        mock_stress_result = [random.uniform(1, 10)]
        mock_report_result = {"status": "critical", "impact_score": random.randint(50, 99)}

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as MockSimulator, \
             patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as MockReporter, \
             patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="{}"):
            
            sim_instance = MockSimulator.return_value
            sim_instance.simulate_scenario.return_value = mock_sim_result
            sim_instance.run_stress_test.return_value = mock_stress_result

            rep_instance = MockReporter.return_value
            rep_instance.run_stress_reporting.return_value = mock_report_result

            result = run_stress_scenario_pipeline(self.storage_file, self.symbol, self.percentage, self.shifts)

            self.assertEqual(result["simulation"]["symbol"], self.symbol)
            self.assertEqual(result["simulation"]["percentage"], self.percentage)
            self.assertEqual(result["stress_test"]["symbol"], self.symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.shifts)
            self.assertIn("results", result["stress_test"])
            self.assertEqual(result["stress_report"]["symbol"], self.symbol)
            self.assertEqual(result["stress_report"]["status"], "critical")

if __name__ == "__main__":
    unittest.main()