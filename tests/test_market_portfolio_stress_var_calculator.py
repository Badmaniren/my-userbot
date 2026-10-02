import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.market_portfolio_stress_var_calculator import (
    StressVarCalculator,
    StressCalculationError
)

class TestStressVarCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_id = str(uuid.uuid4())
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.investment_value = round(random.uniform(10000.0, 1000000.0), 2)

        self.mock_db = MagicMock()
        self.mock_simulator = MagicMock()

        self.calculator = StressVarCalculator(
            db_storage=self.mock_db,
            market_portfolio_scenario_simulator=self.mock_simulator
        )

    def test_calculate_var_and_cvar_success(self):
        random_shocks_count = random.randint(100, 1000)
        simulated_returns = [round(random.normalvariate(-0.02, 0.05), 4) for _ in range(random_shocks_count)]

        self.mock_simulator.run_scenario.return_value = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.scenario_id,
            "returns": simulated_returns
        }

        with patch('skills.market_portfolio_stress_var_calculator.uuid') as mock_uuid:
            generated_run_id = str(uuid.uuid4())
            mock_uuid.uuid4.return_value = generated_run_id

            result = self.calculator.compute_stress_var_cvar(
                portfolio_id=self.portfolio_id,
                scenario_id=self.scenario_id,
                confidence_level=self.confidence_level,
                initial_value=self.investment_value
            )

        self.assertIn("var_value", result)
        self.assertIn("cvar_value", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["scenario_id"], self.scenario_id)
        self.assertGreaterEqual(result["var_value"], 0.0)
        self.assertGreaterEqual(result["cvar_value"], result["var_value"])

        self.mock_db.save_calculation.assert_called_once()

    def test_calculator_handles_empty_simulation_returns(self):
        self.mock_simulator.run_scenario.return_value = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.scenario_id,
            "returns": []
        }

        with self.assertRaises(StressCalculationError):
            self.calculator.compute_stress_var_cvar(
                portfolio_id=self.portfolio_id,
                scenario_id=self.scenario_id,
                confidence_level=self.confidence_level,
                initial_value=self.investment_value
            )

    def test_export_stress_report_stream(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_file_stream = io.BytesIO(random_stream_data)

        with patch.object(self.calculator, '_generate_report_stream', return_value=mock_file_stream) as mock_gen:
            exported_stream = self.calculator.export_stress_report(self.portfolio_id)

            data = exported_stream.read()
            self.assertEqual(data, random_stream_data)
            mock_gen.assert_called_once_with(self.portfolio_id)

    def test_invalid_confidence_level_raises_error(self):
        invalid_confidence = random.choice([-0.5, 0.0, 1.0, 1.5])

        with self.assertRaises(ValueError):
            self.calculator.compute_stress_var_cvar(
                portfolio_id=self.portfolio_id,
                scenario_id=self.scenario_id,
                confidence_level=invalid_confidence,
                initial_value=self.investment_value
            )

if __name__ == '__main__':
    unittest.main()