import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_testing_unified_engine import (
    MarketPortfolioStressTestingUnifiedEngine
)

class TestMarketPortfolioStressTestingUnifiedEngine(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.monte_carlo_engine = MagicMock()
        self.scenario_evaluator = MagicMock()
        self.stress_reporter = MagicMock()
        self.scenario_simulator = MagicMock()
        self.stress_audit_visualizer = MagicMock()

        self.engine = MarketPortfolioStressTestingUnifiedEngine(
            db_storage=self.db_storage,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine,
            market_portfolio_stress_scenario_matrix_evaluator=self.scenario_evaluator,
            market_portfolio_stress_reporter=self.stress_reporter,
            market_portfolio_scenario_simulator=self.scenario_simulator,
            market_portfolio_stress_audit_visualizer=self.stress_audit_visualizer
        )

    def test_execute_unified_stress_testing_pipeline(self):
        portfolio_id = uuid.uuid4().hex
        iterations = random.randint(100, 5000)
        confidence_level = round(random.uniform(0.90, 0.99), 4)

        simulated_paths_count = random.randint(50, 2000)
        monte_carlo_result = {
            "portfolio_id": portfolio_id,
            "paths": simulated_paths_count,
            "var_value": round(random.uniform(1000.0, 50000.0), 2)
        }
        self.monte_carlo_engine.run_simulation.return_value = monte_carlo_result

        scenario_matrix_id = uuid.uuid4().hex
        matrix_evaluation_result = {
            "matrix_id": scenario_matrix_id,
            "max_drawdown": round(random.uniform(0.05, 0.50), 4),
            "passed": random.choice([True, False])
        }
        self.scenario_evaluator.evaluate_matrix.return_value = matrix_evaluation_result

        report_id = uuid.uuid4().hex
        report_output = {
            "report_id": report_id,
            "status": "GENERATED"
        }
        self.stress_reporter.generate_risk_report.return_value = report_output

        fake_uuid = uuid.uuid4()
        execution_run_id = str(fake_uuid)

        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = fake_uuid

            result = self.engine.run_unified_stress_test(
                portfolio_id=portfolio_id,
                iterations=iterations,
                confidence_level=confidence_level
            )

        self.monte_carlo_engine.run_simulation.assert_called_once_with(
            portfolio_id=portfolio_id,
            iterations=iterations,
            confidence_level=confidence_level
        )
        self.scenario_evaluator.evaluate_matrix.assert_called_once_with(
            portfolio_id=portfolio_id,
            monte_carlo_data=monte_carlo_result
        )
        self.stress_reporter.generate_risk_report.assert_called_once_with(
            portfolio_id=portfolio_id,
            monte_carlo_data=monte_carlo_result,
            matrix_evaluation=matrix_evaluation_result
        )

        self.assertIn("execution_id", result)
        self.assertEqual(result["execution_id"], execution_run_id)
        self.assertEqual(result["monte_carlo"], monte_carlo_result)
        self.assertEqual(result["matrix_evaluation"], matrix_evaluation_result)
        self.assertEqual(result["report"], report_output)

    def test_handle_stress_testing_exception_flow(self):
        portfolio_id = uuid.uuid4().hex
        iterations = random.randint(50, 1000)
        confidence_level = round(random.uniform(0.80, 0.98), 4)

        random_error_message = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
        self.monte_carlo_engine.run_simulation.side_effect = RuntimeError(random_error_message)

        with self.assertRaises(RuntimeError) as context:
            self.engine.run_unified_stress_test(
                portfolio_id=portfolio_id,
                iterations=iterations,
                confidence_level=confidence_level
            )

        self.assertIn(random_error_message, str(context.exception))
        self.db_storage.log_error.assert_called()