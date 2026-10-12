import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json

from skills.market_portfolio_stress_resilience_analyzer import (
    MarketPortfolioStressResilienceAnalyzer,
    market_portfolio_stress_resilience_analyzer
)

class TestMarketPortfolioStressResilienceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.simulator_mock = MagicMock()
        self.monitor_mock = MagicMock()

        self.analyzer = MarketPortfolioStressResilienceAnalyzer(
            db_storage=self.db_storage_mock,
            market_portfolio_scenario_simulator=self.simulator_mock,
            market_portfolio_monitor=self.monitor_mock
        )

    def test_evaluate_resilience_success(self):
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())
        expected_impact_score = round(random.uniform(1.0, 100.0), 2)
        expected_metrics = {uuid.uuid4().hex: random.randint(1, 1000)}
        expected_health = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.simulator_mock.run_scenario.return_value = {
            "impact_score": expected_impact_score,
            "metrics": expected_metrics
        }
        self.monitor_mock.get_health_status.return_value = expected_health

        result = self.analyzer.evaluate_resilience(portfolio_id, scenario_id)

        self.assertEqual(result["resilience_score"], expected_impact_score)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["scenario_id"], scenario_id)
        self.assertEqual(result["health_status"], expected_health)
        self.assertEqual(result["scenario_metrics"], expected_metrics)
        self.simulator_mock.run_scenario.assert_called_once_with(scenario_id, portfolio_id)
        self.monitor_mock.get_health_status.assert_called_once()

    def test_evaluate_resilience_exception_logging(self):
        portfolio_id = str(uuid.uuid4())
        scenario_id = str(uuid.uuid4())
        exception_message = uuid.uuid4().hex

        self.simulator_mock.run_scenario.side_effect = Exception(exception_message)

        with self.assertRaises(Exception) as ctx:
            self.analyzer.evaluate_resilience(portfolio_id, scenario_id)

        self.assertIn(exception_message, str(ctx.exception))
        self.db_storage_mock.log_error.assert_called_once_with(exception_message)

    def test_ingest_stream_report_valid_json(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        payload = {random_key: random_val}
        raw_bytes = json.dumps(payload).encode('utf-8')
        stream = io.BytesIO(raw_bytes)

        result = self.analyzer.ingest_stream_report(stream)

        self.assertEqual(result[random_key], random_val)
        self.assertEqual(result["raw_bytes"], raw_bytes)

    def test_ingest_stream_report_invalid_json(self):
        raw_bytes = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(raw_bytes)

        result = self.analyzer.ingest_stream_report(stream)

        self.assertEqual(result, {"raw_bytes": raw_bytes})

    def test_compile_stress_report(self):
        portfolio_id = str(uuid.uuid4())
        fetch_result = {uuid.uuid4().hex: random.randint(100, 500)}
        self.db_storage_mock.fetch_portfolio_data.return_value = fetch_result

        report = self.analyzer.compile_stress_report(portfolio_id)

        self.assertIn("report_id", report)
        self.assertEqual(report["data"], fetch_result)
        self.db_storage_mock.fetch_portfolio_data.assert_called_once_with(portfolio_id)

    def test_functional_analyzer_green_health(self):
        portfolio_id = str(uuid.uuid4())
        sim_val = round(random.uniform(10.0, 500.0), 2)
        corr_factor = round(random.uniform(0.1, 1.0), 2)

        input_data = {
            "portfolio_id": portfolio_id,
            "simulation_data": {"simulated_value": sim_val},
            "subsystem_health": {"health_status": "GREEN"},
            "correlation_factor": corr_factor
        }

        result = market_portfolio_stress_resilience_analyzer(input_data)

        expected_score = round(50.0 + 30.0 + (sim_val * 0.00001) * corr_factor, 2)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["resilience_score"], expected_score)
        self.assertEqual(result["status"], "ANALYZED")

    def test_functional_analyzer_non_green_health(self):
        portfolio_id = str(uuid.uuid4())
        sim_val = round(random.uniform(10.0, 500.0), 2)
        corr_factor = round(random.uniform(0.1, 1.0), 2)
        bad_status = uuid.uuid4().hex

        input_data = {
            "portfolio_id": portfolio_id,
            "simulation_data": {"simulated_value": sim_val},
            "subsystem_health": {"health_status": bad_status},
            "correlation_factor": corr_factor
        }

        result = market_portfolio_stress_resilience_analyzer(input_data)

        expected_score = round(50.0 + (sim_val * 0.00001) * corr_factor, 2)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["resilience_score"], expected_score)
        self.assertEqual(result["status"], "ANALYZED")

if __name__ == '__main__':
    unittest.main()