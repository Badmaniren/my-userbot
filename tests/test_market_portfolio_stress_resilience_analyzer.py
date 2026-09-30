import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_portfolio_stress_resilience_analyzer import start_new


class TestMarketPortfolioStressResilienceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.shock_level = round(random.uniform(1.0, 50.0), 2)
        self.scenario_name = uuid.uuid4().hex

    def test_start_new_anomaly_check_path(self):
        dynamic_scenario = "anomaly_check"
        mock_raw_stream = uuid.uuid4().hex
        mock_analysis_result = {"status": uuid.uuid4().hex, "metric": random.randint(1, 100)}

        with patch("skills.market_anomaly_detector.market_anomaly_detector.fetch_live_data", return_value=mock_raw_stream) as mock_fetch, \
             patch("skills.market_anomaly_detector.market_anomaly_detector.analyze_stream", return_value=mock_analysis_result) as mock_analyze:

            result = start_new(scenario_name=dynamic_scenario)

            mock_fetch.assert_called_once()
            mock_analyze.assert_called_once_with(mock_raw_stream)
            self.assertEqual(result, mock_analysis_result)

    def test_start_new_fallback_collector_agent(self):
        dynamic_scenario = "anomaly_check"
        mock_raw_stream = uuid.uuid4().hex
        mock_analysis_result = {"anomaly_detected": True, "code": uuid.uuid4().hex}

        with patch("skills.market_anomaly_detector.market_anomaly_detector.fetch_live_data", side_effect=AttributeError), \
             patch("skills.market_portfolio_collector_agent.market_portfolio_collector_agent.fetch_live_data", return_value=mock_raw_stream) as mock_collector_fetch, \
             patch("skills.market_anomaly_detector.market_anomaly_detector.analyze_stream", return_value=mock_analysis_result) as mock_analyze:

            result = start_new(scenario_name=dynamic_scenario)

            mock_collector_fetch.assert_called_once()
            mock_analyze.assert_called_once_with(mock_raw_stream)
            self.assertEqual(result, mock_analysis_result)

    def test_start_new_standard_stress_test_flow(self):
        mock_simulation_metrics = {
            "portfolio_id": self.portfolio_id,
            "shock_level": self.shock_level,
            "scenario": self.scenario_name,
            "impact": random.randint(-1000, -100)
        }

        with patch("skills.market_portfolio_scenario_simulator.market_portfolio_scenario_simulator.run_stress_test", return_value=mock_simulation_metrics) as mock_run_test, \
             patch("skills.market_portfolio_stress_reporter.market_portfolio_stress_reporter.generate_report") as mock_generate_report, \
             patch("skills.db_storage.db_storage.save_stress_results") as mock_save_results:

            result = start_new(
                portfolio_id=self.portfolio_id,
                shock_level=self.shock_level,
                scenario_name=self.scenario_name
            )

            mock_run_test.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                intensity=self.shock_level,
                scenario=self.scenario_name
            )
            mock_generate_report.assert_called_once_with(mock_simulation_metrics)
            mock_save_results.assert_called_once_with(mock_simulation_metrics)
            self.assertEqual(result, mock_simulation_metrics)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["shock_level"], self.shock_level)


if __name__ == "__main__":
    unittest.main()