import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_drawdown_analyzer import (
    analyze_drawdowns,
    calculate_ulcer_index,
    evaluate_recovery_period,
    MarketPortfolioDrawdownAnalyzer
)


class TestMarketPortfolioDrawdownAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.db_url = f"sqlite:///{uuid.uuid4().hex}.db"
        self.metric_key = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_float_series = [round(random.uniform(100.0, 1000.0), 2) for _ in range(random.randint(10, 30))]

    def test_analyze_drawdowns_logic(self):
        mock_db = MagicMock()
        mock_gateway = MagicMock()
        mock_gateway.fetch_portfolio_history.return_value = self.random_float_series

        with patch('skills.market_portfolio_drawdown_analyzer.db_storage', mock_db), \
             patch('skills.market_portfolio_drawdown_analyzer.market_portfolio_api_gateway', mock_gateway):

            result = analyze_drawdowns(self.portfolio_id)

            self.assertIn("max_drawdown", result)
            self.assertIsInstance(result["max_drawdown"], float)
            self.assertGreaterEqual(result["max_drawdown"], 0.0)
            mock_gateway.fetch_portfolio_history.assert_called_once_with(self.portfolio_id)

    def test_calculate_ulcer_index_with_garbage_stream(self):
        garbage_bytes = io.BytesIO(uuid.uuid4().bytes * random.randint(2, 5))

        with patch('skills.market_portfolio_drawdown_analyzer.market_parser') as mock_parser:
            mock_parser.parse_stream.return_value = garbage_bytes

            ulcer_result = calculate_ulcer_index(garbage_bytes)
            self.assertIsInstance(ulcer_result, float)

    def test_evaluate_recovery_period_anomaly(self):
        mock_anomaly_detector = MagicMock()
        target_anomaly_score = random.uniform(0.1, 0.9)
        mock_anomaly_detector.detect_anomaly.return_value = target_anomaly_score

        with patch('skills.market_portfolio_drawdown_analyzer.market_anomaly_detector', mock_anomaly_detector):
            evaluation = evaluate_recovery_period(self.portfolio_id, self.random_float_series)

            self.assertEqual(evaluation["anomaly_score"], target_anomaly_score)
            self.assertIn("recovery_status", evaluation)
            mock_anomaly_detector.detect_anomaly.assert_called_once()

    def test_analyzer_class_pipeline_integration(self):
        analyzer = MarketPortfolioDrawdownAnalyzer(db_storage_uri=self.db_url)

        random_endpoint = f"https://{uuid.uuid4().hex}.test/api/v1/metrics"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = f"<html><body><div id='{self.metric_key}'>{random.uniform(10, 50)}</div></body></html>"

        with patch('requests.get', return_value=mock_response) as mock_get:
            res = analyzer.audit_strategy(random_endpoint, self.metric_key)
            self.assertTrue(res["status"])
            mock_get.assert_called_once_with(random_endpoint, timeout=10)

    def test_stress_recovery_coordination_bridge(self):
        mock_bridge = MagicMock()
        expected_status = uuid.uuid4().hex
        mock_bridge.coordinate.return_value = {"status": expected_status}

        with patch('skills.market_portfolio_drawdown_analyzer.market_portfolio_stress_recovery_coordinator_bridge', mock_bridge):
            analyzer = MarketPortfolioDrawdownAnalyzer()
            response = analyzer.trigger_stress_recovery(self.portfolio_id)

            self.assertEqual(response["status"], expected_status)
            mock_bridge.coordinate.assert_called_once_with(self.portfolio_id)


if __name__ == '__main__':
    unittest.main()