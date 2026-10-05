import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_macro_liquidity_collector_v2 import (
    MarketMacroLiquidityCollectorV2,
    LiquidityCollectionError
)


class TestMarketMacroLiquidityCollectorV2(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_extractors = {
            f"extractor_tool_{random.randint(100000000, 999999999)}": MagicMock()
            for _ in range(5)
        }
        self.mock_anomaly_detector = MagicMock()
        self.mock_insider_tracker = MagicMock()
        self.mock_parser = MagicMock()

        self.collector = MarketMacroLiquidityCollectorV2(
            db_storage=self.mock_db,
            market_anomaly_detector=self.mock_anomaly_detector,
            market_parser=self.mock_parser,
            **self.mock_extractors
        )

    def test_collect_macro_liquidity_success(self):
        expected_liquidity_id = str(uuid.uuid4())
        random_metric_value = round(random.uniform(1000.50, 999999.99), 2)
        random_source_url = f"https://{uuid.uuid4().hex}.net/{uuid.uuid4().hex}"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = f'{{"liquidity_id": "{expected_liquidity_id}", "value": {random_metric_value}}}'.encode('utf-8')
        mock_response.json.return_value = {
            "liquidity_id": expected_liquidity_id,
            "value": random_metric_value
        }

        with patch('requests.Session.get', return_value=mock_response) as mock_get:
            result = self.collector.collect_liquidity_metric(random_source_url)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("liquidity_id"), expected_liquidity_id)
            self.assertEqual(result.get("value"), random_metric_value)
            mock_get.assert_called_once_with(random_source_url, timeout=unittest.mock.ANY)
            self.mock_db.save_liquidity_record.assert_called_once()

    def test_collect_macro_liquidity_network_failure(self):
        random_error_url = f"https://{uuid.uuid4().hex}.org/api/{uuid.uuid4().hex}"

        with patch('requests.Session.get', side_effect=Exception(uuid.uuid4().hex)) as mock_get:
            with self.assertRaises(LiquidityCollectionError):
                self.collector.collect_liquidity_metric(random_error_url)

            mock_get.assert_called_once()
            self.mock_db.save_liquidity_record.assert_not_called()

    def test_parse_macro_stream_with_random_bytes(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        random_parser_target = uuid.uuid4().hex
        self.mock_parser.parse_stream.return_value = {
            "target": random_parser_target,
            "status": "parsed"
        }

        parsed_result = self.collector.process_stream_data(mock_stream)

        self.assertIsInstance(parsed_result, dict)
        self.assertEqual(parsed_result.get("target"), random_parser_target)
        self.mock_parser.parse_stream.assert_called_once()

    def test_anomaly_detection_integration(self):
        random_anomaly_score = random.uniform(0.0, 100.0)
        random_payload_id = str(uuid.uuid4())

        self.mock_anomaly_detector.evaluate.return_value = {
            "anomaly_score": random_anomaly_score,
            "id": random_payload_id,
            "flagged": random_anomaly_score > 50.0
        }

        evaluation_output = self.collector.run_anomaly_check({
            "id": random_payload_id,
            "metric": random.randint(1, 100)
        })

        self.assertEqual(evaluation_output["id"], random_payload_id)
        self.assertAlmostEqual(evaluation_output["anomaly_score"], random_anomaly_score)
        self.mock_anomaly_detector.evaluate.assert_called_once()


if __name__ == '__main__':
    unittest.main()