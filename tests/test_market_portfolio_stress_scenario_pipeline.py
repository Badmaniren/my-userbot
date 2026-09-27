import unittest
from unittest.mock import patch
import io
import json
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):
    def test_portfolio_stress_scenario_pipeline_execute(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-50.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(random.randint(2, 5))]

        sim_val = round(random.uniform(100.0, 10000.0), 2)
        stress_test_res = [round(random.uniform(-100.0, 100.0), 2) for _ in shifts]
        stress_rep_res = f"report_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
             patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter") as mock_rep_cls:
            
            mock_sim_instance = mock_sim_cls.return_value
            mock_sim_instance.simulate_scenario.return_value = {"symbol": symbol, "simulated_value": sim_val}
            mock_sim_instance.run_stress_test.return_value = {"symbol": symbol, "results": stress_test_res}

            mock_rep_instance = mock_rep_cls.return_value
            mock_rep_instance.run_stress_report.return_value = {"symbol": symbol, "report": stress_rep_res}

            pipeline = PortfolioStressScenarioPipeline(storage_file)
            result = pipeline.execute(symbol, percentage, shifts)

            self.assertIn("simulation", result)
            self.assertIn("stress_test", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["results"], stress_test_res)
            self.assertEqual(result["stress_report"]["report"], stress_rep_res)
            mock_sim_instance.simulate_scenario.assert_called_once_with(symbol, percentage)
            mock_sim_instance.run_stress_test.assert_called_once_with(symbol, shifts)
            mock_rep_instance.run_stress_report.assert_called_once_with(symbol, shifts)

    def test_run_stress_scenario_pipeline_success(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-30.0, 30.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2) for _ in range(3)]

        file_content = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        sim_val = round(random.uniform(500.0, 5000.0), 2)
        stress_res = [round(random.uniform(-10.0, 10.0), 2) for _ in shifts]
        impact_score = random.randint(1, 100)

        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.return_value = file_content

            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

                mock_sim = mock_sim_cls.return_value
                mock_sim.simulate_scenario.return_value = {"symbol": symbol, "simulated_value": sim_val}
                mock_sim.run_stress_test.return_value = {"symbol": symbol, "results": stress_res}

                mock_rep = mock_rep_cls.return_value
                mock_rep.run_stress_reporting.return_value = {"symbol": symbol, "impact_score": impact_score}

                result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

                self.assertEqual(result["simulation"]["simulated_value"], sim_val)
                self.assertEqual(result["stress_test"]["results"], stress_res)
                self.assertEqual(result["stress_report"]["impact_score"], impact_score)

    def test_run_stress_scenario_pipeline_exception_handling(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-20.0, 20.0), 2)
        shifts = [round(random.uniform(-2.0, 2.0), 2) for _ in range(2)]

        with patch("builtins.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            mock_file.read.side_effect = Exception(uuid.uuid4().hex)

            with patch("skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator") as mock_sim_cls, \
                 patch("skills.market_portfolio_stress_scenario_pipeline.StressReporter") as mock_rep_cls:

                mock_sim = mock_sim_cls.return_value
                mock_sim.simulate_scenario.side_effect = KeyError(uuid.uuid4().hex)
                mock_sim.run_stress_test.side_effect = KeyError(uuid.uuid4().hex)

                mock_rep = mock_rep_cls.return_value
                mock_rep.run_stress_reporting.side_effect = Exception(uuid.uuid4().hex)

                result = run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts)

                self.assertEqual(result["simulation"]["simulated_value"], 0.0)
                self.assertEqual(result["simulation"]["symbol"], symbol)
                self.assertEqual(result["stress_test"]["results"], [])
                self.assertEqual(result["stress_report"]["status"], "default")
                self.assertEqual(result["stress_report"]["impact_score"], 0)

if __name__ == "__main__":
    unittest.main()