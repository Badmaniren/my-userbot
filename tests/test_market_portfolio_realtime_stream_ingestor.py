import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_realtime_stream_ingestor import start_new

class TestMarketPortfolioRealtimeStreamIngestor(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            f"dep_{uuid.uuid4().hex[:8]}": MagicMock()
            for _ in range(70)
        }
        self.random_stream_id = uuid.uuid4().hex
        self.random_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.random_byte_data = self.random_payload.encode('utf-8')

    def test_start_new_success_flow(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "stream_id": self.random_stream_id,
            "status": "VALID",
            "payload": self.random_payload
        }

        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser,
            "market_portfolio_collector_agent": MagicMock()
        }

        with patch("skills.market_portfolio_realtime_stream_ingestor.io.BytesIO", return_value=io.BytesIO(self.random_byte_data)) as mock_io:
            result = start_new(context, stream_source=self.random_stream_id)

        self.assertIsNotNone(result)
        mock_parser.parse.assert_called_once()
        mock_db.save.assert_called_once()
        saved_args = mock_db.save.call_args[0][0]
        self.assertEqual(saved_args["stream_id"], self.random_stream_id)
        self.assertEqual(saved_args["payload"], self.random_payload)

    def test_start_new_validation_failure(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "stream_id": self.random_stream_id,
            "status": "INVALID",
            "error": "CORRUPTED_STREAM"
        }

        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser,
            "market_portfolio_audit_log_exporter": MagicMock()
        }

        corrupted_bytes = uuid.uuid4().bytes + random.randbytes(16)
        with patch("skills.market_portfolio_realtime_stream_ingestor.io.BytesIO", return_value=io.BytesIO(corrupted_bytes)):
            result = start_new(context, stream_source=self.random_stream_id)

        self.assertEqual(result.get("status"), "REJECTED")
        mock_db.save.assert_not_called()

    def test_start_new_exception_handling(self):
        mock_db = MagicMock()
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception(f"Stream failure {uuid.uuid4().hex}")

        context = {
            "db_storage": mock_db,
            "market_parser": mock_parser,
            "market_portfolio_alert_dispatcher": MagicMock()
        }

        with patch("skills.market_portfolio_realtime_stream_ingestor.io.BytesIO", return_value=io.BytesIO(self.random_byte_data)):
            with self.assertRaises(Exception):
                start_new(context, stream_source=self.random_stream_id)

        mock_db.save.assert_not_called()

if __name__ == "__main__":
    unittest.main()