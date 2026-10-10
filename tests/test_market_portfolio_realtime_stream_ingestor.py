import unittest
from unittest.mock import MagicMock, patch
import io
import os
import json
import uuid
import random
import string
from skills.market_portfolio_realtime_stream_ingestor import start_new, market_portfolio_realtime_stream_ingestor

class TestMarketPortfolioRealtimeStreamIngestor(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_parser = MagicMock()
        self.mock_detector = MagicMock()
        self.context = {
            "db_storage": self.mock_db,
            "market_parser": self.mock_parser,
            "market_anomaly_detector": self.mock_detector
        }

    def test_start_new_success_flow(self):
        random_id = uuid.uuid4().hex
        random_payload = {"event_id": random_id, "status": "VALID", "data": random.random()}
        stream_data = json.dumps(random_payload)
        
        self.mock_parser.parse.return_value = random_payload
        
        result = start_new(self.context, stream_source=stream_data)
        
        self.assertEqual(result.get("event_id"), random_id)
        self.mock_db.save.assert_called_once_with(random_payload)

    def test_start_new_invalid_status(self):
        random_id = uuid.uuid4().hex
        stream_data = json.dumps({"event_id": random_id})
        self.mock_parser.parse.return_value = {"status": "INVALID"}
        
        result = start_new(self.context, stream_source=stream_data)
        
        self.assertEqual(result.get("status"), "REJECTED")
        self.mock_db.save.assert_not_called()

    def test_start_new_exception_propagation(self):
        stream_data = "".join(random.choices(string.ascii_letters, k=10))
        self.mock_parser.parse.side_effect = ValueError("Critical parsing failure")
        
        with self.assertRaises(ValueError):
            start_new(self.context, stream_source=stream_data)

    def test_market_portfolio_realtime_stream_ingestor_file_io(self):
        random_dir = uuid.uuid4().hex
        random_file = f"{random_dir}/{uuid.uuid4().hex}.json"
        random_event_id = uuid.uuid4().hex
        payload = {"event_id": random_event_id, "val": random.uniform(0, 1000)}
        
        with patch("os.makedirs") as mock_makedirs:
            with patch("builtins.open", unittest.mock.mock_open()) as mocked_file:
                result = market_portfolio_realtime_stream_ingestor(payload, random_file)

                self.assertEqual(result["processed_id"], random_event_id)
                self.assertEqual(result["status"], "SUCCESS")

                mock_makedirs.assert_called_once()
                mocked_file.assert_called_once_with(random_file, "w", encoding="utf-8")

                handle = mocked_file()
                written_data = json.loads(handle.write.call_args[0][0])
                self.assertEqual(written_data["event_id"], random_event_id)

    def test_stream_ingestion_with_anomaly_detection_logic(self):
        # Проверка интеграции детектора аномалий
        random_val = random.randint(100, 999)
        payload = {"value": random_val, "status": "VALID"}
        self.mock_parser.parse.return_value = payload
        
        # Симуляция вызова
        result = start_new(self.context, stream_source=json.dumps(payload))
        
        self.assertEqual(result["value"], random_val)
        self.assertTrue(self.mock_db.save.called)

if __name__ == "__main__":
    unittest.main()