import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_scenario_pipeline import (
    run_stress_scenario_pipeline,
    PortfolioStressScenarioPipeline
)

class TestMarketPortfolioStressScenarioPipeline(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"data_{uuid.uuid4().hex}.json"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_percentage = round(random.uniform(-50.0, 50.0), 2)
        self.random_shifts = [round(random.uniform(-20.0, 20.0), 2) for _ in range(random.randint(2, 5))]
        self.random_report_output = {
            "symbol": self.random_symbol,
            "status": uuid.uuid4().hex,
            "impact_score": random.randint(1, 100)
        }

    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter')
    def test_pipeline_composition_run(self, mock_stress_reporter_cls, mock_simulator_cls):
        mock_simulator_instance = mock_simulator_cls.return_value
        mock_simulator_instance.simulate_scenario.return_value = {
            "symbol": self.random_symbol,
            "percentage": self.random_percentage,
            "simulated_value": random.randint(100, 1000)
        }

        mock_reporter_instance = mock_stress_reporter_cls.return_value
        mock_reporter_instance.run_stress_reporting.return_value = self.random_report_output

        result = run_stress_scenario_pipeline(
            self.random_storage,
            self.random_symbol,
            self.random_percentage,
            self.random_shifts
        )

        mock_simulator_cls.assert_called_once_with(self.random_storage)
        mock_simulator_instance.simulate_scenario.assert_called_once_with(
            self.random_symbol, self.random_percentage
        )
        mock_simulator_instance.run_stress_test.assert_called_once_with(
            self.random_symbol, self.random_shifts
        )

        mock_stress_reporter_cls.assert_called_once_with(self.random_storage)
        mock_reporter_instance.run_stress_reporting.assert_called_once_with(
            self.random_symbol, self.random_shifts
        )

        self.assertIn("simulation", result)
        self.assertIn("stress_test", result)
        self.assertIn("stress_report", result)
        self.assertEqual(result["stress_report"], self.random_report_output)

    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressReporter')
    def test_pipeline_class_execution(self, mock_portfolio_reporter_cls, mock_simulator_cls):
        mock_sim_inst = mock_simulator_cls.return_value
        sim_result_data = {
            "uuid": uuid.uuid4().hex,
            "target": self.random_symbol,
            "drop": self.random_percentage
        }
        mock_sim_inst.run_stress_test.return_value = sim_result_data

        mock_rep_inst = mock_portfolio_reporter_cls.return_value
        report_result_data = {
            "report_id": uuid.uuid4().hex,
            "data": self.random_shifts
        }
        mock_rep_inst.run_stress_report.return_value = report_result_data

        pipeline = PortfolioStressScenarioPipeline(self.random_storage)
        execution_result = pipeline.execute(
            self.random_symbol,
            self.random_percentage,
            self.random_shifts
        )

        mock_simulator_cls.assert_called_once_with(self.random_storage)
        mock_portfolio_reporter_cls.assert_called_once_with(self.random_storage)

        mock_sim_inst.simulate_scenario.assert_called_once_with(
            self.random_symbol, self.random_percentage
        )
        mock_sim_inst.run_stress_test.assert_called_once_with(
            self.random_symbol, self.random_shifts
        )
        mock_rep_inst.run_stress_report.assert_called_once_with(
            self.random_symbol, self.random_shifts
        )

        self.assertEqual(execution_result["stress_test"], sim_result_data)
        self.assertEqual(execution_result["stress_report"], report_result_data)

    @patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_stress_scenario_pipeline.StressReporter')
    def test_pipeline_error_handling(self, mock_stress_reporter_cls, mock_simulator_cls):
        error_message = f"critical_failure_{uuid.uuid4().hex}"
        mock_simulator_instance = mock_simulator_cls.return_value
        mock_simulator_instance.simulate_scenario.side_effect = Exception(error_message)

        with self.assertRaises(Exception) as context:
            run_stress_scenario_pipeline(
                self.random_storage,
                self.random_symbol,
                self.random_percentage,
                self.random_shifts
            )

        self.assertIn(error_message, str(context.exception))

if __name__ == '__main__':
    unittest.main()