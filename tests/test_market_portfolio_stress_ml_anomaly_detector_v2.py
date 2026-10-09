import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.market_portfolio_stress_ml_anomaly_detector_v2 import (
    AnomalyDetectionError,
    MarketPortfolioStressMLAnomalyDetectorV2,
    market_portfolio_stress_ml_anomaly_detector_v2
)

class TestMarketPortfolioStressMLAnomalyDetectorV2(unittest.TestCase):
    def setUp(self):
        self.random_url = f"http://{uuid.uuid4().hex}.com/api"
        self.portfolio_id = uuid.uuid4().hex
        self.detector = MarketPortfolioStressMLAnomalyDetectorV2(collector_agent_url=self.random_url)

    @patch('skills.market_portfolio_stress_ml_anomaly_detector_v2.requests.get')
    def test_detect_anomalies_success(self, mock_get):
        anomaly_flag = random.choice([True, False])
        mock_response = MagicMock()
        mock_response.json.return_value = [{"is_anomaly": anomaly_flag, "id": self.portfolio_id}]
        mock_get.return_value = mock_response

        result = self.detector.detect_anomalies(portfolio_id=self.portfolio_id)

        expected_url = f"{self.random_url}?portfolio_id={self.portfolio_id}"
        mock_get.assert_called_once_with(expected_url, timeout=10)
        self.assertIsInstance(result, list)
        if anomaly_flag:
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0]["is_anomaly"])
        else:
            self.assertEqual(len(result), 0)

    def test_detect_anomalies_url_with_query(self):
        url_with_query = f"http://{uuid.uuid4().hex}.com/api?active=true"
        detector = MarketPortfolioStressMLAnomalyDetectorV2(collector_agent_url=url_with_query)

        with patch('skills.market_portfolio_stress_ml_anomaly_detector_v2.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"is_anomaly": True}
            mock_get.return_value = mock_response

            detector.detect_anomalies(portfolio_id=self.portfolio_id)
            expected_url = f"{url_with_query}&portfolio_id={self.portfolio_id}"
            mock_get.assert_called_once_with(expected_url, timeout=10)

    @patch('skills.market_portfolio_stress_ml_anomaly_detector_v2.requests.get')
    def test_detect_anomalies_request_exception(self, mock_get):
        mock_get.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(AnomalyDetectionError):
            self.detector.detect_anomalies(portfolio_id=self.portfolio_id)

    def test_parse_collector_stream_with_read(self):
        random_hex = uuid.uuid4().hex
        random_text = f"<html><body><div>{random_hex}</div></body></html>"
        stream_mock = io.BytesIO(random_text.encode('utf-8'))

        parsed = self.detector.parse_collector_stream(stream_mock)
        self.assertIn("raw_content", parsed)
        self.assertIn(random_hex[:5], parsed["raw_content"] or random_text)

    def test_parse_collector_stream_bytes(self):
        random_bytes = uuid.uuid4().bytes
        parsed = self.detector.parse_collector_stream(random_bytes)
        self.assertIn("raw_content", parsed)

    def test_score_stress_metrics_empty(self):
        scores = self.detector.score_stress_metrics([])
        self.assertEqual(scores, [])

    def test_score_stress_metrics_normal(self):
        data_points = [random.uniform(0.1, 10.0) for _ in range(5)]
        scores = self.detector.score_stress_metrics(data_points)
        self.assertEqual(len(scores), len(data_points))
        for score in scores:
            self.assertTrue(0.0 <= score <= 1.0)


class TestMarketPortfolioStressMLAnomalyDetectorV2Integration(unittest.TestCase):
    def test_integration_dict_input(self):
        input_data = {
            "volatility": random.uniform(0.0, 1.0),
            "stress_loss": random.uniform(0.0, 1.0),
            "liquidity_index": random.uniform(0.0, 1.0)
        }
        result = market_portfolio_stress_ml_anomaly_detector_v2(input_data)
        self.assertIsInstance(result, dict)
        self.assertIn("anomaly_detected", result)
        self.assertIn("confidence_score", result)
        self.assertIsInstance(result["anomaly_detected"], bool)
        self.assertIsInstance(result["confidence_score"], float)

    def test_integration_list_input(self):
        input_data = [
            {"val1": random.uniform(0.0, 5.0)},
            {"val2": random.uniform(0.0, 5.0)}
        ]
        result = market_portfolio_stress_ml_anomaly_detector_v2(input_data)
        self.assertIsInstance(result, dict)
        self.assertIn("anomaly_detected", result)
        self.assertIn("confidence_score", result)

    def test_integration_invalid_input(self):
        invalid_input = uuid.uuid4().hex
        result = market_portfolio_stress_ml_anomaly_detector_v2(invalid_input)
        self.assertEqual(result["anomaly_detected"], False)
        self.assertEqual(result["confidence_score"], 0.0)

    def test_integration_exception_handling(self):
        with patch('skills.market_portfolio_stress_ml_anomaly_detector_v2.MarketPortfolioStressMLAnomalyDetectorV2.score_stress_metrics', side_effect=ValueError(uuid.uuid4().hex)):
            with self.assertRaises(AnomalyDetectionError):
                market_portfolio_stress_ml_anomaly_detector_v2({"volatility": 0.5})

if __name__ == '__main__':
    unittest.main()