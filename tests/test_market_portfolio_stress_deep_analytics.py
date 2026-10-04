import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import string
import io

from skills.market_portfolio_stress_deep_analytics import (
    MarketPortfolioStressDeepAnalytics,
    run_deep_stress_analytics
)


class TestMarketPortfolioStressDeepAnalytics(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"
        self.scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
        self.target_asset = f"asset_{uuid.uuid4().hex[:8]}"
        self.anomaly_token = f"token_{uuid.uuid4().hex[:8]}"

        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.liquidity_analyzer = MagicMock()
        self.scenario_simulator = MagicMock()

        self.analytics = MarketPortfolioStressDeepAnalytics(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_liquidity_scenario_analyzer=self.liquidity_analyzer,
            market_portfolio_scenario_simulator=self.scenario_simulator
        )

    def test_collect_historical_deviations_success(self):
        expected_data = {f"metric_{uuid.uuid4().hex[:4]}": random.uniform(-10, 10)}
        self.db_storage.fetch_history.return_value = [expected_data]

        result = self.analytics.collect_historical_deviations(self.portfolio_id)
        self.assertEqual(result, expected_data)
        self.db_storage.fetch_history.assert_called_once_with(self.portfolio_id)

    def test_collect_historical_deviations_empty(self):
        self.db_storage.fetch_history.return_value = []
        result = self.analytics.collect_historical_deviations(self.portfolio_id)
        self.assertEqual(result, {})

    def test_collect_historical_deviations_no_db(self):
        analytics_no_db = MarketPortfolioStressDeepAnalytics(db_storage=None)
        result = analytics_no_db.collect_historical_deviations(self.portfolio_id)
        self.assertEqual(result, {})

    def test_generate_structured_liquidity_forecast(self):
        sim_gap = random.uniform(100, 5000)
        sim_result = {"liquidity_gap": sim_gap, "status": "simulated"}
        analysis_res = {"evaluated": True, "risk": "high"}
        history_res = {"deviation": random.uniform(0, 1)}

        self.scenario_simulator.run_simulation.return_value = sim_result
        self.liquidity_analyzer.evaluate.return_value = analysis_res
        self.db_storage.fetch_history.return_value = [history_res]

        forecast = self.analytics.generate_structured_liquidity_forecast(self.scenario_id, self.target_asset)

        self.assertEqual(forecast["scenario_id"], self.scenario_id)
        self.assertEqual(forecast["target_asset"], self.target_asset)
        self.assertEqual(forecast["liquidity_gap"], sim_gap)
        self.assertEqual(forecast["simulation"], sim_result)
        self.assertEqual(forecast["analysis"], analysis_res)
        self.assertEqual(forecast["historical_deviations"], history_res)

        self.scenario_simulator.run_simulation.assert_called_once_with(self.scenario_id)
        self.liquidity_analyzer.evaluate.assert_called_once_with(sim_result)
        self.db_storage.fetch_history.assert_called_once_with(self.scenario_id)

    def test_audit_market_anomalies(self):
        scan_data = {f"anomaly_{uuid.uuid4().hex[:4]}": True}
        self.anomaly_detector.scan.return_value = scan_data

        result = self.analytics.audit_market_anomalies(self.anomaly_token)
        self.assertEqual(result, scan_data)
        self.anomaly_detector.scan.assert_called_once_with(self.anomaly_token)

    def test_aggregate_extractor_payloads(self):
        data_1 = {f"k1_{uuid.uuid4().hex[:4]}": random.randint(1, 10)}
        data_2 = {f"k2_{uuid.uuid4().hex[:4]}": random.randint(11, 20)}
        data_3 = {f"k3_{uuid.uuid4().hex[:4]}": random.randint(21, 30)}
        data_4 = {f"k4_{uuid.uuid4().hex[:4]}": random.randint(31, 40)}

        self.extractor_1.extract.return_value = data_1
        self.extractor_2.extract.return_value = data_2
        self.extractor_3.extract.return_value = data_3
        self.extractor_4.extract.return_value = data_4

        aggregated = self.analytics.aggregate_extractor_payloads()

        expected = {}
        expected.update(data_1)
        expected.update(data_2)
        expected.update(data_3)
        expected.update(data_4)

        self.assertEqual(aggregated, expected)
        self.extractor_1.extract.assert_called_once()
        self.extractor_2.extract.assert_called_once()
        self.extractor_3.extract.assert_called_once()
        self.extractor_4.extract.assert_called_once()

    def test_run_deep_stress_analytics(self):
        volatility = random.uniform(0.1, 0.9)
        stress_factor = random.uniform(1.0, 5.0)
        liquidity_data = {f"liq_{uuid.uuid4().hex[:4]}": random.random()}
        monte_carlo_data = {f"mc_{uuid.uuid4().hex[:4]}": random.random()}

        payload = {
            "portfolio_id": self.portfolio_id,
            "historical_volatility": volatility,
            "stress_factor": stress_factor,
            "liquidity_data": liquidity_data,
            "monte_carlo_data": monte_carlo_data
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                result = run_deep_stress_analytics(payload)

                mock_makedirs.assert_called_once_with("data/stress_reports", exist_ok=True)
                mock_file.assert_called_once()
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertEqual(result["historical_volatility"], volatility)
                self.assertEqual(result["stress_factor"], stress_factor)
                self.assertEqual(result["liquidity_data"], liquidity_data)
                self.assertEqual(result["monte_carlo_data"], monte_carlo_data)
                self.assertEqual(result["status"], "COMPLETED")
                self.assertIn("forecast_id", result)


if __name__ == "__main__":
    unittest.main()