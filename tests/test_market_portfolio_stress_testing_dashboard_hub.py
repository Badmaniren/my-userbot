import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_testing_dashboard_hub import start_new

class TestMarketPortfolioStressTestingDashboardHub(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            f"dep_{uuid.uuid4().hex[:8]}": MagicMock()
            for _ in range(58)
        }
        self.db_storage = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_stress_reporter = MagicMock()
        
        self.random_portfolio_id = uuid.uuid4().hex
        self.random_simulation_runs = random.randint(100, 10000)
        self.random_confidence_level = round(random.uniform(0.90, 0.99), 4)

    def test_start_new_success_flow(self):
        mock_monte_carlo_result = {
            "portfolio_id": self.random_portfolio_id,
            "runs": self.random_simulation_runs,
            "var": round(random.uniform(1000.0, 50000.0), 2),
            "status": "completed"
        }
        
        mock_scenario_result = {
            "scenario_id": uuid.uuid4().hex,
            "impact_score": round(random.uniform(-0.5, 0.0), 4)
        }

        self.market_portfolio_stress_monte_carlo_engine.run.return_value = mock_monte_carlo_result
        self.market_portfolio_scenario_simulator.evaluate.return_value = mock_scenario_result

        kwargs = {
            "db_storage": self.db_storage,
            "market_anomaly_detector": self.market_anomaly_detector,
            "market_portfolio_stress_monte_carlo_engine": self.market_portfolio_stress_monte_carlo_engine,
            "market_portfolio_scenario_simulator": self.market_portfolio_scenario_simulator,
            "portfolio_id": self.random_portfolio_id,
            "simulations": self.random_simulation_runs,
            "confidence": self.random_confidence_level
        }

        with patch("skills.market_portfolio_stress_testing_dashboard_hub.uuid") as mock_uuid:
            generated_dashboard_id = uuid.uuid4().hex
            mock_uuid.uuid4.return_value.hex = generated_dashboard_id

            result = start_new(**kwargs)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("dashboard_id"), generated_dashboard_id)
            self.assertEqual(result.get("portfolio_id"), self.random_portfolio_id)
            self.assertEqual(result.get("monte_carlo"), mock_monte_carlo_result)
            self.assertEqual(result.get("scenario"), mock_scenario_result)
            
            self.market_portfolio_stress_monte_carlo_engine.run.assert_called_once()
            self.market_portfolio_scenario_simulator.evaluate.assert_called_once()

    def test_start_new_handles_exceptions_gracefully(self):
        random_error_message = ''.join(random.choices(string.ascii_letters + string.space, k=20))
        self.market_portfolio_stress_monte_carlo_engine.run.side_effect = Exception(random_error_message)

        kwargs = {
            "db_storage": self.db_storage,
            "market_anomaly_detector": self.market_anomaly_detector,
            "market_portfolio_stress_monte_carlo_engine": self.market_portfolio_stress_monte_carlo_engine,
            "portfolio_id": self.random_portfolio_id
        }

        result = start_new(**kwargs)

        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertEqual(result["error"], random_error_message)
        self.assertEqual(result.get("status"), "failed")

    def test_start_new_io_stream_handling(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters, k=50)).encode('utf-8')
        mock_file_stream = io.BytesIO(random_stream_data)

        self.db_storage.read_blob.return_value = mock_file_stream

        kwargs = {
            "db_storage": self.db_storage,
            "market_anomaly_detector": self.market_anomaly_detector,
            "market_portfolio_stress_monte_carlo_engine": self.market_portfolio_stress_monte_carlo_engine,
            "data_stream": mock_file_stream,
            "portfolio_id": self.random_portfolio_id
        }

        result = start_new(**kwargs)

        self.assertIsInstance(result, dict)
        self.db_storage.read_blob.assert_not_called()

    def test_start_new_with_multiple_random_aggregations(self):
        random_metrics_count = random.randint(1, 10)
        mock_metrics = [
            {uuid.uuid4().hex: random.uniform(0, 100)} 
            for _ in range(random_metrics_count)
        ]

        self.market_portfolio_stress_reporter.aggregate.return_value = mock_metrics

        kwargs = {
            "db_storage": self.db_storage,
            "market_portfolio_stress_reporter": self.market_portfolio_stress_reporter,
            "portfolio_id": self.random_portfolio_id
        }

        result = start_new(**kwargs)

        self.assertIsInstance(result, dict)
        self.market_portfolio_stress_reporter.aggregate.assert_called_once()

    def test_start_new_empty_arguments(self):
        result = start_new()
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

if __name__ == "__main__":
    unittest.main()