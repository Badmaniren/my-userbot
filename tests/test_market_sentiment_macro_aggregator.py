import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.market_sentiment_macro_aggregator import start_new

class TestMarketSentimentMacroAggregator(unittest.TestCase):

    def setUp(self):
        self.dependencies = {
            f"dep_{uuid.uuid4().hex[:6]}": MagicMock()
            for _ in range(45)
        }

    def test_start_new_success_flow(self):
        target_id = uuid.uuid4().hex
        random_macro_value = random.uniform(-100.0, 100.0)
        random_text_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32))

        mock_db = MagicMock()
        mock_db.fetch_latest.return_value = {
            "id": target_id,
            "macro_score": random_macro_value,
            "payload": random_text_payload
        }

        self.dependencies["db_storage"] = mock_db

        with patch("skills.market_sentiment_macro_aggregator.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "active",
                "data_stream": random_text_payload,
                "metric": random_macro_value
            }
            mock_response.content = io.BytesIO(random_text_payload.encode('utf-8')).read()
            mock_get.return_value = mock_response

            result = start_new(self.dependencies)

            self.assertIsNotNone(result)
            mock_db.fetch_latest.assert_called()
            mock_get.assert_called()

    def test_start_new_failure_handling(self):
        random_error_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        random_error_msg = "".join(random.choices(string.ascii_lowercase, k=16))

        mock_parser = MagicMock()
        mock_parser.parse_feed.side_effect = Exception(random_error_msg)
        self.dependencies["market_parser"] = mock_parser

        with patch("skills.market_sentiment_macro_aggregator.uuid.uuid4") as mock_uuid:
            err_uuid = uuid.uuid4()
            mock_uuid.return_value = err_uuid

            with self.assertRaises(Exception) as ctx:
                start_new(self.dependencies)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_start_new_edge_cases_empty_payloads(self):
        random_sentinel_key = f"sentinel_{uuid.uuid4().hex[:8]}"
        mock_sentinel = MagicMock()
        mock_sentinel.check_status.return_value = {}
        self.dependencies["market_portfolio_autonomous_sentinel"] = mock_sentinel

        with patch("skills.market_sentiment_macro_aggregator.bs4.BeautifulSoup") as mock_bs:
            mock_soup_instance = MagicMock()
            mock_soup_instance.text = ""
            mock_bs.return_value = mock_soup_instance

            res = start_new(self.dependencies)
            self.assertTrue(res is None or isinstance(res, (dict, list, str, int, float, bool)))
            mock_sentinel.check_status.assert_called()

    def test_start_new_random_heavy_aggregation(self):
        metric_key = f"metric_{uuid.uuid4().hex[:5]}"
        expected_metric_val = random.randint(1000, 99999)

        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.return_value = {metric_key: expected_metric_val}
        self.dependencies["market_portfolio_predictive_aggregator"] = mock_aggregator

        with patch("skills.market_sentiment_macro_aggregator.random.choice") as mock_rand_choice:
            mock_rand_choice.return_value = metric_key

            output = start_new(self.dependencies)

            if isinstance(output, dict):
                self.assertIn(metric_key, output)
                self.assertEqual(output[metric_key], expected_metric_val)
            else:
                mock_aggregator.aggregate.assert_called()

if __name__ == "__main__":
    unittest.main()