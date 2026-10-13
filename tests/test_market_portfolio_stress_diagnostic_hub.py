import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_diagnostic_hub import MarketPortfolioStressDiagnosticHub


class TestMarketPortfolioStressDiagnosticHub(unittest.TestCase):

    def setUp(self):
        self.mock_deps = {
            "db_storage": MagicMock(),
            "market_portfolio_stress_scenario_executor_bridge": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_stress_resilience_optimizer": MagicMock()
        }
        self.hub = MarketPortfolioStressDiagnosticHub(**self.mock_deps)

    def test_run_diagnostic_success(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_scenario_metric = random.randint(1000, 99999)
        rand_stress_report_key = "".join(random.choices(string.ascii_lowercase, k=10))

        stress_payload = {
            rand_stress_report_key: rand_scenario_metric,
            "timestamp": random.randint(1500000000, 1800000000)
        }

        with patch.object(self.mock_deps["db_storage"], "save_metric", return_value=True) as mock_save:
            result = self.hub.run_diagnostic(rand_portfolio_id, stress_payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["status"], "COMPLETED")
            self.assertIn("resilience_score", result)
            self.assertIsInstance(result["recommendations"], list)
            self.assertTrue(len(result["recommendations"]) > 0)

    def test_run_diagnostic_invalid_inputs(self):
        invalid_portfolio = ""
        empty_payload = {}

        with self.assertRaises(ValueError):
            self.hub.run_diagnostic(invalid_portfolio, empty_payload)

    def test_diagnostic_with_stream_mock_io(self):
        rand_portfolio_id = uuid.uuid4().hex
        random_bytes_content = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")

        fake_stream = io.BytesIO(random_bytes_content)

        stress_payload = {
            "stream_data": fake_stream.read().decode("utf-8"),
            "entropy": random.random()
        }

        result = self.hub.run_diagnostic(rand_portfolio_id, stress_payload)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertIn("diagnostic_id", result)

if __name__ == "__main__":
    unittest.main()