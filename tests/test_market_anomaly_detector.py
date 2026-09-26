import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import os

from skills.market_anomaly_detector import (
    MarketAnomalyDetector,
    process_anomaly_stream,
    strict_parse_anomaly,
    market_anomaly_detector
)

class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.run_id = uuid.uuid4().hex
        self.marker_file = f"anomaly_{self.run_id}.log"

    def tearDown(self):
        if os.path.exists(self.marker_file):
            os.remove(self.marker_file)

    def test_market_anomaly_detector_initialization(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        detector = MarketAnomalyDetector(**{key: val})
        self.assertEqual(getattr(detector, key), val)

    def test_process_anomaly_stream_empty(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            process_anomaly_stream(empty_stream)

    def test_process_anomaly_stream_malformed(self):
        malformed_stream = io.BytesIO(b"A" * 16)
        with self.assertRaises(ValueError):
            process_anomaly_stream(malformed_stream)

    @patch('skills.market_anomaly_detector.requests.get')
    def test_process_anomaly_stream_success(self, mock_get):
        random_bytes = uuid.uuid4().bytes
        if len(random_bytes) == 16:
            random_bytes = b"abc123xyz789"
        stream = io.BytesIO(random_bytes)

        expected_json = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_json
        mock_get.return_value = mock_response

        result = process_anomaly_stream(stream)
        self.assertEqual(result, expected_json)
        mock_get.assert_called_once()

    def test_strict_parse_anomaly_failures(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            strict_parse_anomaly(empty_stream)

        malformed_stream = io.BytesIO(b"B" * 16)
        with self.assertRaises(ValueError):
            strict_parse_anomaly(malformed_stream)

    def test_strict_parse_anomaly_success(self):
        payload = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(payload)
        res = strict_parse_anomaly(stream)
        self.assertEqual(res, payload.decode('utf-8'))

    def test_market_anomaly_detector_invalid_type(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            market_anomaly_detector(invalid_data)

    def test_market_anomaly_detector_logic_anomaly(self):
        price_factor = random.uniform(50.1, 500.0)
        volume = random.randint(100, 400000)
        parsed_data = {
            "run_id": self.run_id,
            "price_factor": price_factor,
            "volume": volume
        }

        result = market_anomaly_detector(parsed_data)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["run_id"], self.run_id)
        self.assertTrue(os.path.exists(self.marker_file))

        with open(self.marker_file, "r") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["run_id"], self.run_id)
            self.assertTrue(file_data["anomaly_detected"])

    def test_market_anomaly_detector_logic_normal(self):
        price_factor = random.uniform(0.1, 49.9)
        volume = random.randint(10, 400000)
        parsed_data = {
            "run_id": self.run_id,
            "price_factor": price_factor,
            "volume": volume
        }

        result = market_anomaly_detector(parsed_data)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["run_id"], self.run_id)
        self.assertTrue(os.path.exists(self.marker_file))

        with open(self.marker_file, "r") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["run_id"], self.run_id)
            self.assertFalse(file_data["anomaly_detected"])

if __name__ == '__main__':
    unittest.main()