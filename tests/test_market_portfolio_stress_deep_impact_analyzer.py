import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys

from skills.market_portfolio_stress_deep_impact_analyzer import (
    MarketPortfolioStressDeepImpactAnalyzer
)

class TestMarketPortfolioStressDeepImpactAnalyzer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.scenario_evaluator = MagicMock()
        self.monte_carlo_engine = MagicMock()
        self.alert_dispatcher = MagicMock()

        self.analyzer = MarketPortfolioStressDeepImpactAnalyzer(
            db_storage=self.db_storage,
            scenario_evaluator=self.scenario_evaluator,
            monte_carlo_engine=self.monte_carlo_engine,
            alert_dispatcher=self.alert_dispatcher
        )

    def test_analyze_deep_impact_success_flow(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = "".join(random.choices(string.ascii_uppercase, k=8))
        simulations_count = random.randint(1000, 5000)

        expected_matrix_score = round(random.uniform(0.1, 9.9), 4)
        expected_var = round(random.uniform(1000.0, 50000.0), 2)

        self.scenario_evaluator.evaluate_matrix.return_value = {
            "matrix_score": expected_matrix_score,
            "status": "COMPLETED"
        }

        self.monte_carlo_engine.run_simulation.return_value = {
            "var_95": expected_var,
            "simulations": simulations_count
        }

        with patch("skills.market_portfolio_stress_deep_impact_analyzer.datetime") as mock_dt:
            random_timestamp = "".join(random.choices(string.digits, k=10))
            mock_dt.now.return_value.isoformat.return_value = random_timestamp

            result = self.analyzer.analyze_deep_impact(portfolio_id, scenario_code, simulations_count)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["scenario_code"], scenario_code)
        self.assertEqual(result["matrix_score"], expected_matrix_score)
        self.assertEqual(result["var_95"], expected_var)

        self.db_storage.save_impact_analysis.assert_called_once()
        self.alert_dispatcher.dispatch_alert.assert_not_called()

    def test_analyze_deep_impact_triggers_high_risk_alert(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        simulations_count = random.randint(500, 2000)

        critical_matrix_score = round(random.uniform(9.0, 10.0), 4)

        self.scenario_evaluator.evaluate_matrix.return_value = {
            "matrix_score": critical_matrix_score,
            "status": "CRITICAL_BREACH"
        }

        self.monte_carlo_engine.run_simulation.return_value = {
            "var_95": round(random.uniform(100000.0, 999999.0), 2),
            "simulations": simulations_count
        }

        result = self.analyzer.analyze_deep_impact(portfolio_id, scenario_code, simulations_count)

        self.assertEqual(result["matrix_score"], critical_matrix_score)
        self.assertTrue(result["alert_triggered"])
        self.alert_dispatcher.dispatch_alert.assert_called_once()

    def test_load_portfolio_matrix_stream_parsing(self):
        random_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_file_stream = io.BytesIO(random_stream_data)

        with patch("skills.market_portfolio_stress_deep_impact_analyzer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_stream_data
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.market-metrics.internal/matrix"
            parsed_data = self.analyzer.load_external_matrix_stream(random_url)

            self.assertIn("stream_hash", parsed_data)
            self.assertEqual(parsed_data["raw_bytes_length"], len(random_stream_data))
            mock_get.assert_called_once_with(random_url, timeout=10)

    def test_exception_handling_during_monte_carlo_failure(self):
        portfolio_id = str(uuid.uuid4())
        scenario_code = "".join(random.choices(string.ascii_lowercase, k=6))

        self.scenario_evaluator.evaluate_matrix.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(RuntimeError):
            self.analyzer.analyze_deep_impact(portfolio_id, scenario_code, 100)

        self.db_storage.save_impact_analysis.assert_not_called()
        self.alert_dispatcher.dispatch_alert.assert_not_called()

if __name__ == "__main__":
    unittest.main()