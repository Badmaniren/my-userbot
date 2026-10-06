import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_portfolio_deep_stress_analyzer import (
    MarketPortfolioDeepStressAnalyzer,
    StressAnalysisError
)

class TestMarketPortfolioDeepStressAnalyzer(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.simulations_count = random.randint(100, 1000)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)

        self.db_storage_mock = MagicMock()
        self.monte_carlo_mock = MagicMock()
        self.reporter_mock = MagicMock()
        self.simulator_mock = MagicMock()
        self.var_core_mock = MagicMock()

        self.analyzer = MarketPortfolioDeepStressAnalyzer(
            db_storage=self.db_storage_mock,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_mock,
            market_portfolio_stress_reporter=self.reporter_mock,
            market_portfolio_scenario_simulator=self.simulator_mock,
            market_portfolio_var_liquidity_core=self.var_core_mock
        )

    def test_analyze_portfolio_success(self):
        mc_output = {"monte_carlo_metric": random.randint(500, 5000)}
        var_output = {"var_value": round(random.uniform(10.0, 500.0), 2)}
        report_output = {"report_status": f"status_{uuid.uuid4().hex[:6]}"}

        self.monte_carlo_mock.run_simulation.return_value = mc_output
        self.var_core_mock.calculate_var.return_value = var_output
        self.reporter_mock.generate_report.return_value = report_output

        result = self.analyzer.analyze_portfolio(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations_count,
            confidence=self.confidence_level
        )

        self.monte_carlo_mock.run_simulation.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations_count,
            confidence=self.confidence_level
        )
        self.var_core_mock.calculate_var.assert_called_once_with(portfolio_id=self.portfolio_id)
        self.reporter_mock.generate_report.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            data={**mc_output, **var_output}
        )
        self.db_storage_mock.save_analysis.assert_called_once()

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["monte_carlo_results"], mc_output)
        self.assertEqual(result["var_results"], var_output)
        self.assertEqual(result["report"], report_output)
        self.assertIn("analysis_id", result)

    def test_analyze_portfolio_raises_stress_analysis_error(self):
        self.monte_carlo_mock.run_simulation.side_effect = Exception(f"err_{uuid.uuid4().hex[:8]}")

        with self.assertRaises(StressAnalysisError):
            self.analyzer.analyze_portfolio(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations_count,
                confidence=self.confidence_level
            )

    def test_fetch_and_aggregate_external_stream(self):
        random_url = f"https://{uuid.uuid4().hex[:8]}.com/stream"
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_override = random.randint(1000, 9999)
        binary_data = uuid.uuid4().bytes * random.randint(1, 5)

        with patch("skills.market_portfolio_deep_stress_analyzer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [binary_data]
            mock_get.return_value = mock_response

            result = self.analyzer.fetch_and_aggregate_external_stream(
                url=random_url,
                extraction_key=random_key,
                override_value=random_override
            )

            mock_get.assert_called_once_with(random_url, stream=True, timeout=10)
            self.assertEqual(result["stream_size"], len(binary_data))
            self.assertEqual(result["injected_metric"], random_override)

    def test_perform_deep_analysis(self):
        metrics_dict = {f"metric_{uuid.uuid4().hex[:4]}": random.random()}
        raw_payload = f"raw_{uuid.uuid4().hex[:6]}"

        result = self.analyzer.perform_deep_analysis(
            portfolio_id=self.portfolio_id,
            metrics=metrics_dict,
            raw_data=raw_payload
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["metrics"], metrics_dict)
        self.assertEqual(result["status"], "processed")
        self.assertIn("report_id", result)
        self.assertTrue(result["report_id"].startswith("rep_"))

if __name__ == "__main__":
    unittest.main()