import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_var_event_streamer import MarketPortfolioVaREventStreamer

class TestMarketPortfolioVaREventStreamer(unittest.TestCase):
    def setUp(self):
        self.streamer_id = str(uuid.uuid4())
        self.endpoint_url = f"https://{uuid.uuid4().hex}.example.com/api/v1/var-stream"
        self.streamer = MarketPortfolioVaREventStreamer(
            streamer_id=self.streamer_id,
            endpoint_url=self.endpoint_url
        )

    def test_initialization_state(self):
        self.assertEqual(self.streamer.streamer_id, self.streamer_id)
        self.assertEqual(self.streamer.endpoint_url, self.endpoint_url)
        self.assertFalse(self.streamer.is_streaming)
        self.assertEqual(self.streamer.event_counter, 0)

    def test_generate_var_event_payload(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        var_value = round(random.uniform(1000.0, 500000.0), 2)
        currency = random.choice(["USD", "EUR", "GBP", "JPY", "CHF"])

        payload = self.streamer.generate_var_event_payload(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level,
            var_value=var_value,
            currency=currency
        )

        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["streamer_id"], self.streamer_id)
        self.assertEqual(payload["portfolio_id"], portfolio_id)
        self.assertEqual(payload["confidence_level"], confidence_level)
        self.assertEqual(payload["var_value"], var_value)
        self.assertEqual(payload["currency"], currency)
        self.assertIn("timestamp", payload)
        self.assertIn("event_uuid", payload)

    def test_stream_event_success(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        var_value = round(random.uniform(500.0, 150000.0), 2)

        mock_response_data = {
            "status": "success",
            "ack_id": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_var_event_streamer.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = self.streamer.stream_event(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                var_value=var_value
            )

            mock_post.assert_called_once()
            self.assertTrue(result)
            self.assertEqual(self.streamer.event_counter, 1)

    def test_stream_event_http_error(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        var_value = round(random.uniform(100.0, 10000.0), 2)

        with patch("skills.market_portfolio_var_event_streamer.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = random.choice([400, 401, 403, 500, 502])
            mock_post.return_value = mock_resp

            result = self.streamer.stream_event(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                var_value=var_value
            )

            self.assertFalse(result)
            self.assertEqual(self.streamer.event_counter, 0)

    def test_stream_event_network_exception(self):
        portfolio_id = str(uuid.uuid4())
        confidence_level = round(random.uniform(0.90, 0.99), 4)
        var_value = round(random.uniform(100.0, 10000.0), 2)

        with patch("skills.market_portfolio_var_event_streamer.requests.post") as mock_post:
            mock_post.side_effect = Exception(uuid.uuid4().hex)

            result = self.streamer.stream_event(
                portfolio_id=portfolio_id,
                confidence_level=confidence_level,
                var_value=var_value
            )

            self.assertFalse(result)
            self.assertEqual(self.streamer.event_counter, 0)

    def test_batch_stream_events(self):
        events_count = random.randint(2, 5)
        portfolio_ids = [str(uuid.uuid4()) for _ in range(events_count)]

        with patch("skills.market_portfolio_var_event_streamer.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"status": "batch_received"}
            mock_post.return_value = mock_resp

            success_count = self.streamer.batch_stream_events(portfolio_ids)

            self.assertEqual(success_count, events_count)
            self.assertEqual(self.streamer.event_counter, events_count)

    def test_export_metrics_stream(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_file_stream = io.BytesIO(random_bytes)

        exported_data = self.streamer.export_metrics_stream(mock_file_stream)

        self.assertIsInstance(exported_data, dict)
        self.assertEqual(exported_data["streamer_id"], self.streamer_id)
        self.assertEqual(exported_data["bytes_processed"], len(random_bytes))
        self.assertIn("checksum", exported_data)

if __name__ == "__main__":
    unittest.main()