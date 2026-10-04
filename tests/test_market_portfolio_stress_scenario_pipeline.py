import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline, run_stress_scenario_pipeline

class TestPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_percentage = round(random.uniform(-50.0, 50.0), 2)
        self.random_shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

    def test_load_or_create_storage_creates_file_on_exception(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                pipeline._load_or_create_storage()

    def test_execute_pipeline_success(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        
        sim_val = round(random.uniform(10.0, 1000.0), 2)
        mock_sim_result = {"simulated_value": sim_val}
        mock_stress_res = [round(random.uniform(1.0, 5.0), 2)]
        mock_rep_res = {"status": "ok", "impact_score": random.randint(1, 100)}

        with patch.object(pipeline.simulator, 'simulate_scenario', return_value=mock_sim_result) as mock_sim, \
             patch.object(pipeline.simulator, 'run_stress_test', return_value=mock_stress_res) as mock_stress, \
             patch.object(pipeline.reporter, 'run_stress_report', return_value=mock_rep_res) as mock_rep, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps({uuid.uuid4().hex: random.randint(1, 10)})
            mock_open.return_value.__enter__.return_value = mock_file

            result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)

            mock_sim.assert_called_once_with(self.random_symbol, self.random_percentage)
            mock_stress.assert_called_once_with(self.random_symbol, self.random_shifts)
            mock_rep.assert_called_once_with(self.random_symbol, self.random_shifts)

            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], sim_val)
            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["shifts"], self.random_shifts)
            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_report"]["status"], "ok")

    def test_execute_pipeline_handles_key_errors(self):
        pipeline = PortfolioStressScenarioPipeline(self.random_storage)

        with patch.object(pipeline.simulator, 'simulate_scenario', side_effect=KeyError), \
             patch.object(pipeline.simulator, 'run_stress_test', side_effect=KeyError), \
             patch.object(pipeline.reporter, 'run_stress_report', side_effect=RuntimeError), \
             patch('builtins.open', create=True) as mock_open:

            mock_file = MagicMock()
            mock_file.read.return_value = "{}"
            mock_open.return_value.__enter__.return_value = mock_file

            result = pipeline.execute(self.random_symbol, self.random_percentage, self.random_shifts)

            self.assertEqual(result["simulation"]["symbol"], self.random_symbol)
            self.assertEqual(result["simulation"]["simulated_value"], 0.0)
            self.assertEqual(result["stress_test"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_test"]["results"], [])
            self.assertEqual(result["stress_report"]["symbol"], self.random_symbol)
            self.assertEqual(result["stress_report"]["status"], "default")
            self.assertEqual(result["stress_report"]["impact_score"], 0)

    def test_functional_pipeline_runner(self):
        sim_val = round(random.uniform(50.0, 500.0), 2)
        mock_sim_result = {"symbol": self.random_symbol, "simulated_value": sim_val}
        mock_stress_res = {"results": [random.randint(1, 10)]}
        mock_rep_res = {"symbol": self.random_symbol, "status": "warning", "impact_score": random.randint(50, 99)}

        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator') as MockSimClass, \
             patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter') as MockRepClass, \
             patch('builtins.open', create=True) as mock_open:

            mock_sim_instance = MockSimClass.return_value
            mock_sim_instance.simulate_scenario.return_value = mock_sim_result
            mock_sim_instance.run_stress_test.return_value = mock_stress_res

            mock_rep_instance = MockRepClass.return_value
            mock_rep_instance.run_stress_reporting.return_value = mock_rep_res

            mock_file = MagicMock()
            mock_file.read.return_value = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})
            mock_open.return_value.__enter__.return_value = mock_file

            res = run_stress_scenario_pipeline(self.random_storage, self.random_symbol, self.random_percentage, self.random_shifts)

            self.assertEqual(res["simulation"]["simulated_value"], sim_val)
            self.assertEqual(res["stress_report"]["status"], "warning")
            self.assertIn("results", res["stress_test"])

if __name__ == '__main__':
    unittest.main()