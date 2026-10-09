import sys
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

try:
    import requests
except ImportError:
    requests = MagicMock()
    sys.modules['requests'] = requests

from skills.market_portfolio_stress_ml_anomaly_scoring_engine import (
    MarketPortfolioStressMLAnomalyScoringEngine,
    market_portfolio_stress_ml_anomaly_scoring_engine_func
)

class TestMarketPortfolioStressMLAnomalyScoringEngine(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool = MagicMock()
        self.market_anomaly_detector = MagicMock()
        self.market_insider_activity_tracker = MagicMock()
        self.market_news_sentiment_analyzer = MagicMock()
        self.market_parser = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_scenario_simulator = MagicMock()
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()

        self.engine = MarketPortfolioStressMLAnomalyScoringEngine(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool,
            market_anomaly_detector=self.market_anomaly_detector,
            market_insider_activity_tracker=self.market_insider_activity_tracker,
            market_news_sentiment_analyzer=self.market_news_sentiment_analyzer,
            market_parser=self.market_parser,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_scenario_simulator=self.market_portfolio_scenario_simulator,
            market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine
        )

    def test_compute_anomaly_score_success(self):
        portfolio_id = uuid.uuid4().hex
        expected_volatility = round(random.uniform(0.1, 0.9), 4)
        raw_score = round(random.uniform(1.0, 50.0), 2)
        multiplier = round(random.uniform(1.1, 3.0), 2)

        self.db_storage.fetch_historical_volatility.return_value = expected_volatility
        self.market_anomaly_detector.evaluate_matrix.return_value = {"anomaly_score": raw_score}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"multiplier": multiplier}

        with patch.object(requests, "get", return_value=mock_response) as mock_get:
            result = self.engine.compute_anomaly_score(portfolio_id)
            mock_get.assert_called_once_with("https://api.example.com/market-multiplier")

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["volatility"], expected_volatility)
        self.assertEqual(result["score"], raw_score * multiplier)
        self.db_storage.fetch_historical_volatility.assert_called_once_with(portfolio_id)
        self.market_anomaly_detector.evaluate_matrix.assert_called_once_with(portfolio_id)

    def test_compute_anomaly_score_api_failure(self):
        portfolio_id = uuid.uuid4().hex
        expected_volatility = round(random.uniform(0.01, 0.5), 4)
        raw_score = round(random.uniform(5.0, 100.0), 2)

        self.db_storage.fetch_historical_volatility.return_value = expected_volatility
        self.market_anomaly_detector.evaluate_matrix.return_value = {"anomaly_score": raw_score}

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(requests, "get", return_value=mock_response):
            result = self.engine.compute_anomaly_score(portfolio_id)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["volatility"], expected_volatility)
        self.assertEqual(result["score"], raw_score)

    def test_evaluate_stream_anomaly(self):
        analysis_id = uuid.uuid4().hex
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        parsed_data = {"stream_token": uuid.uuid4().hex}
        is_anomaly_flag = random.choice([True, False])

        self.market_parser.parse_stream.return_value = parsed_data
        self.market_insider_activity_tracker.analyze.return_value = {"is_anomaly": is_anomaly_flag}

        result = self.engine.evaluate_stream_anomaly(analysis_id, stream_data)

        self.assertEqual(result["analysis_id"], analysis_id)
        self.assertEqual(result["anomaly_detected"], is_anomaly_flag)
        self.market_parser.parse_stream.assert_called_once_with(stream_data)
        self.market_insider_activity_tracker.analyze.assert_called_once_with(parsed_data)

    def test_market_portfolio_stress_ml_anomaly_scoring_engine_func_default(self):
        payload = {}
        result = market_portfolio_stress_ml_anomaly_scoring_engine_func(payload)

        self.assertIn("anomaly_score_id", result)
        self.assertIn("portfolio_uuid", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["scenario_simulation"], {})
        self.assertEqual(result["forecast_data"], {})

    def test_market_portfolio_stress_ml_anomaly_scoring_engine_func_custom(self):
        custom_uuid = uuid.uuid4().hex
        scenario = {uuid.uuid4().hex: uuid.uuid4().hex}
        forecast = {uuid.uuid4().hex: random.randint(1, 100)}
        payload = {
            "portfolio_uuid": custom_uuid,
            "scenario_simulation": scenario,
            "forecast_data": forecast
        }

        result = market_portfolio_stress_ml_anomaly_scoring_engine_func(payload)

        self.assertEqual(result["portfolio_uuid"], custom_uuid)
        self.assertEqual(result["scenario_simulation"], scenario)
        self.assertEqual(result["forecast_data"], forecast)
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["anomaly_score_id"], str)
        self.assertTrue(len(result["anomaly_score_id"]) > 0)


class TestMarketPortfolioStressMLAnomalyScoringEngineIntegration(unittest.TestCase):
    def test_integration_workflow(self):
        db_storage = MagicMock()
        extractor_tool = MagicMock()
        market_anomaly_detector = MagicMock()
        market_insider_activity_tracker = MagicMock()
        market_news_sentiment_analyzer = MagicMock()
        market_parser = MagicMock()
        market_portfolio_monitor = MagicMock()
        market_portfolio_scenario_simulator = MagicMock()
        market_portfolio_stress_monte_carlo_engine = MagicMock()

        engine = MarketPortfolioStressMLAnomalyScoringEngine(
            db_storage=db_storage,
            extractor_tool_1790087207=extractor_tool,
            market_anomaly_detector=market_anomaly_detector,
            market_insider_activity_tracker=market_insider_activity_tracker,
            market_news_sentiment_analyzer=market_news_sentiment_analyzer,
            market_parser=market_parser,
            market_portfolio_monitor=market_portfolio_monitor,
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine
        )

        portfolio_id = uuid.uuid4().hex
        vol = round(random.uniform(0.05, 0.99), 5)
        score_val = round(random.uniform(10.0, 500.0), 2)
        mult = 1.5

        db_storage.fetch_historical_volatility.return_value = vol
        market_anomaly_detector.evaluate_matrix.return_value = {"anomaly_score": score_val}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"multiplier": mult}

        with patch.object(requests, "get", return_value=mock_resp):
            score_res = engine.compute_anomaly_score(portfolio_id)

        self.assertEqual(score_res["score"], score_val * mult)
        self.assertEqual(score_res["volatility"], vol)

        analysis_id = uuid.uuid4().hex
        stream = io.BytesIO(uuid.uuid4().bytes)
        parsed = {"parsed": uuid.uuid4().hex}
        market_parser.parse_stream.return_value = parsed
        market_insider_activity_tracker.analyze.return_value = {"is_anomaly": True}

        stream_res = engine.evaluate_stream_anomaly(analysis_id, stream)
        self.assertTrue(stream_res["anomaly_detected"])

        func_payload = {
            "portfolio_uuid": portfolio_id,
            "scenario_simulation": {"test": uuid.uuid4().hex},
            "forecast_data": {"vol": vol}
        }
        func_res = market_portfolio_stress_ml_anomaly_scoring_engine_func(func_payload)
        self.assertEqual(func_res["portfolio_uuid"], portfolio_id)
        self.assertEqual(func_res["status"], "success")

if __name__ == "__main__":
    unittest.main()