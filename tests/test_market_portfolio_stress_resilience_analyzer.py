import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_stress_resilience_analyzer import start_new


class TestMarketPortfolioStressResilienceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            f"dep_{uuid.uuid4().hex[:8]}": MagicMock()
            for _ in range(53)
        }
        self.mock_db_storage = MagicMock()
        self.mock_scenario_simulator = MagicMock()
        self.mock_stress_reporter = MagicMock()

    def test_start_new_success_execution(self):
        portfolio_id = str(uuid.uuid4())
        shock_level = round(random.uniform(10.0, 99.9), 2)
        scenario_name = "".join(random.choices(string.ascii_lowercase, k=10))
        
        expected_metrics = {
            "portfolio_id": portfolio_id,
            "scenario": scenario_name,
            "resilience_score": round(random.uniform(0.0, 100.0), 2),
            "max_drawdown": -round(random.uniform(5.0, 50.0), 2),
            "status": "COMPLETED"
        }

        with patch('skills.market_portfolio_stress_resilience_analyzer.market_portfolio_scenario_simulator') as mock_sim, \
             patch('skills.market_portfolio_stress_resilience_analyzer.market_portfolio_stress_reporter') as mock_rep, \
             patch('skills.market_portfolio_stress_resilience_analyzer.db_storage') as mock_db:

            mock_sim.run_stress_test.return_value = expected_metrics
            mock_rep.generate_report.return_value = io.BytesIO(uuid.uuid4().bytes)
            mock_db.save_stress_results.return_value = True

            result = start_new(
                portfolio_id=portfolio_id,
                shock_level=shock_level,
                scenario_name=scenario_name,
                **self.dependencies
            )

            self.assertIsNotNone(result)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("scenario"), scenario_name)
            self.assertEqual(result.get("status"), "COMPLETED")
            self.assertIn("resilience_score", result)

            mock_sim.run_stress_test.assert_called_once_with(portfolio_id=portfolio_id, intensity=shock_level, scenario=scenario_name)
            mock_db.save_stress_results.assert_called_once()

    def test_start_new_handles_failure_gracefully(self):
        invalid_portfolio_id = str(uuid.uuid4())
        random_error_msg = "".join(random.choices(string.ascii_letters + string.space, k=15))

        with patch('skills.market_portfolio_stress_resilience_analyzer.market_portfolio_scenario_simulator') as mock_sim:
            mock_sim.run_stress_test.side_effect = Exception(random_error_msg)

            with self.assertRaises(Exception) as context:
                start_new(
                    portfolio_id=invalid_portfolio_id,
                    shock_level=random.uniform(1.0, 5.0),
                    scenario_name="".join(random.choices(string.ascii_uppercase, k=5)),
                    **self.dependencies
                )

            self.assertIn(random_error_msg, str(context.exception))

    def test_start_new_data_integrity_check(self):
        dynamic_id = uuid.uuid4().hex
        dynamic_threshold = round(random.uniform(0.1, 0.9), 4)
        raw_stream_data = f"data_stream_{uuid.uuid4().hex}".encode('utf-8')

        with patch('skills.market_portfolio_stress_resilience_analyzer.market_portfolio_collector_agent') as mock_collector, \
             patch('skills.market_portfolio_stress_resilience_analyzer.market_anomaly_detector') as mock_detector:

            mock_collector.fetch_live_data.return_value = io.BytesIO(raw_stream_data)
            mock_detector.analyze_stream.return_value = {
                "id": dynamic_id,
                "anomaly_detected": True,
                "threshold": dynamic_threshold
            }

            result = start_new(
                portfolio_id=dynamic_id,
                shock_level=dynamic_threshold,
                scenario_name="anomaly_check",
                **self.dependencies
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("id"), dynamic_id)
            self.assertTrue(result.get("anomaly_detected"))
            self.assertEqual(result.get("threshold"), dynamic_threshold)
            mock_collector.fetch_live_data.assert_called_once()
            mock_detector.analyze_stream.assert_called_once()

if __name__ == '__main__':
    unittest.main()