import unittest
from unittest.mock import MagicMock, patch
import os
import io
import json
import uuid
import random
import string
from skills.market_portfolio_realtime_stream_ingestor import start_new, market_portfolio_realtime_stream_ingestor


class TestMarketPortfolioRealtimeStreamIngestor(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex
        self.output_dir = os.path.join(os.getcwd(), f"test_audit_{self.random_prefix}")
        self.output_file = os.path.join(self.output_dir, f"audit_{uuid.uuid4().hex}.json")

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.output_dir):
            os.rmdir(self.output_dir)

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        
        expected_id = uuid.uuid4().hex
        parsed_mock_data = {"status": "SUCCESS", "event_id": expected_id, "price": random.uniform(10.0, 1000.0)}
        mock_parser.parse.return_value = parsed_mock_data
        
        stream_content = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser
        }
        
        result = start_new(context, stream_source=stream_content)
        
        mock_parser.parse.assert_called_once()
        mock_db.save.assert_called_once_with(parsed_mock_data)
        self.assertEqual(result.get("event_id"), expected_id)
        self.assertEqual(result.get("status"), "SUCCESS")

    def test_start_new_invalid_status_flow(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        
        mock_parser.parse.return_value = {"status": "INVALID"}
        
        stream_content = ''.join(random.choices(string.ascii_letters, k=8))
        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser
        }
        
        result = start_new(context, stream_source=stream_content)
        
        mock_parser.parse.assert_called_once()
        mock_db.save.assert_not_called()
        self.assertEqual(result, {"status": "REJECTED"})

    def test_start_new_exception_propagation(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        
        error_message = f"Parser failure {uuid.uuid4().hex}"
        mock_parser.parse.side_effect = RuntimeError(error_message)
        
        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser
        }
        
        with self.assertRaises(RuntimeError) as ctx:
            start_new(context, stream_source="corrupted_stream")
            
        self.assertIn(error_message, str(ctx.exception))
        mock_db.save.assert_not_called()

    def test_market_portfolio_realtime_stream_ingestor_audit_file_creation(self):
        event_id = uuid.uuid4().hex
        payload = {
            "event_id": event_id,
            "metric_value": random.randint(100, 9999),
            "source": uuid.uuid4().hex
        }
        
        result = market_portfolio_realtime_stream_ingestor(payload, self.output_file)
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["processed_id"], event_id)
        
        self.assertTrue(os.path.exists(self.output_file))
        
        with open(self.output_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data.get("event_id"), event_id)
        self.assertEqual(saved_data.get("metric_value"), payload["metric_value"])
        self.assertEqual(saved_data.get("source"), payload["source"])


if __name__ == "__main__":
    unittest.main()