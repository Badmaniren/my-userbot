import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

class TestMarketPortfolioStressTestingDashboardHub(unittest.TestCase):

    def test_start_new_successful_execution(self):
        portfolio_id = uuid.uuid4().hex
        simulations_count = random.randint(100, 5000)
        confidence_level = round(random.uniform(0.80, 0.99), 2)

        mock_mc_result = {"var": random.random(), "cvar": random.random()}
        mock_scenario_result = {"scenario_id": uuid.uuid4().hex, "impact": -random.random()}
        mock_aggregated_metrics = {"total_risk_score": random.randint(1, 100)}

        monte_carlo_engine = MagicMock()
        monte_carlo_engine.run.return_value = mock_mc_result

        scenario_simulator = MagicMock()
        scenario_simulator.evaluate.return_value = mock_scenario_result

        stress_reporter = MagicMock()
        stress_reporter.aggregate.return_value = mock_aggregated_metrics

        db_storage = MagicMock()
        data_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        from skills.market_portfolio_stress_testing_dashboard_hub import start_new

        response = start_new(
            db_storage=db_storage,
            market_portfolio_stress_monte_carlo_engine=monte_carlo_engine,
            market_portfolio_scenario_simulator=scenario_simulator,
            market_portfolio_stress_reporter=stress_reporter,
            portfolio_id=portfolio_id,
            simulations=simulations_count,
            confidence=confidence_level,
            data_stream=data_stream
        )

        self.assertEqual(response["status"], "completed")
        self.assertEqual(response["portfolio_id"], portfolio_id)
        self.assertIn("dashboard_id", response)
        self.assertEqual(response["monte_carlo"], mock_mc_result)
        self.assertEqual(response["scenario"], mock_scenario_result)
        self.assertEqual(response["aggregated_metrics"], mock_aggregated_metrics)

        db_storage.read_blob.assert_not_called()
        monte_carlo_engine.run.assert_called_once_with(
            portfolio_id=portfolio_id,
            simulations=simulations_count,
            confidence=confidence_level
        )
        scenario_simulator.evaluate.assert_called_once_with(portfolio_id=portfolio_id)
        stress_reporter.aggregate.assert_called_once()

    def test_start_new_handles_db_storage_fallback(self):
        portfolio_id = uuid.uuid4().hex
        db_storage = MagicMock()

        from skills.market_portfolio_stress_testing_dashboard_hub import start_new

        response = start_new(
            db_storage=db_storage,
            portfolio_id=portfolio_id,
            data_stream=None
        )

        self.assertEqual(response["status"], "completed")
        db_storage.read_blob.assert_called_once()

    def test_start_new_handles_exceptions_gracefully(self):
        portfolio_id = uuid.uuid4().hex
        random_error_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=20))

        monte_carlo_engine = MagicMock()
        monte_carlo_engine.run.side_effect = RuntimeError(random_error_message)

        from skills.market_portfolio_stress_testing_dashboard_hub import start_new

        response = start_new(
            market_portfolio_stress_monte_carlo_engine=monte_carlo_engine,
            portfolio_id=portfolio_id
        )

        self.assertEqual(response["status"], "failed")
        self.assertEqual(response["portfolio_id"], portfolio_id)
        self.assertIn(random_error_message, response["error"])
        self.assertIn("dashboard_id", response)

    def test_market_portfolio_stress_testing_dashboard_hub_integration(self):
        dashboard_id = uuid.uuid4().hex
        portfolio_id = uuid.uuid4().hex
        monte_carlo_data = {"result": random.randint(1000, 9999)}
        scenario_data = {"test_metric": random.random()}

        mock_persistent_db = MagicMock()

        with patch("skills.db_storage.db_storage", mock_persistent_db, create=True):
            from skills.market_portfolio_stress_testing_dashboard_hub import market_portfolio_stress_testing_dashboard_hub

            result = market_portfolio_stress_testing_dashboard_hub(
                dashboard_id=dashboard_id,
                portfolio_id=portfolio_id,
                monte_carlo_data=monte_carlo_data,
                scenario_data=scenario_data
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["dashboard_id"], dashboard_id)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["aggregated_metrics"]["monte_carlo"], monte_carlo_data)
            self.assertEqual(result["aggregated_metrics"]["scenario"], scenario_data)
            mock_persistent_db.assert_called_once()