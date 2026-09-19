import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_alert_pipeline import MarketAlertPipeline
from skills.market_parser import MarketParser
from skills.db_storage import DBStorage


class TestMarketAlertPipelineInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5)) + str(random.randint(100, 999))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_threshold = round(random.uniform(5001.0, 10000.0), 2)
        self.random_storage_path = f"{uuid.uuid4().hex}.json"

    def test_pipeline_composition_and_initialization(self):
        pipeline = MarketAlertPipeline(storage_file=self.random_storage_path)

        self.assertTrue(hasattr(pipeline, 'parser'))
        self.assertTrue(hasattr(pipeline, 'storage'))
        self.assertIsInstance(pipeline.parser, MarketParser)
        self.assertIsInstance(pipeline.storage, DBStorage)

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_check_price_threshold_triggers_alert(self, mock_fetch_price):
        mock_fetch_price.return_value = self.random_price

        pipeline = MarketAlertPipeline(storage_file=self.random_storage_path)

        with patch.object(pipeline.storage, 'get_threshold', return_value=self.random_threshold):
            with patch.object(pipeline.storage, 'save_alert') as mock_save_alert:
                alert_generated = pipeline.process_and_check(
                    symbol=self.random_symbol,
                    url=self.random_url,
                    threshold=self.random_price - 1.0
                )

                self.assertTrue(alert_generated)
                mock_fetch_price.assert_called_once_with(self.random_url)
                mock_save_alert.assert_called_once()

    @patch('skills.market_parser.MarketParser.fetch_price')
    def test_check_price_threshold_no_alert(self, mock_fetch_price):
        mock_fetch_price.return_value = self.random_price

        pipeline = MarketAlertPipeline(storage_file=self.random_storage_path)

        with patch.object(pipeline.storage, 'save_alert') as mock_save_alert:
            alert_generated = pipeline.process_and_check(
                symbol=self.random_symbol,
                url=self.random_url,
                threshold=self.random_price + 100.0
            )

            self.assertFalse(alert_generated)
            mock_fetch_price.assert_called_once_with(self.random_url)
            mock_save_alert.assert_not_called()

    @patch('skills.market_parser.MarketParser.parse_html_prices')
    def test_pipeline_batch_processing_with_io_stream(self, mock_parse_html):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_parse_html.return_value = [
            {"symbol": self.random_symbol, "price": self.random_price}
        ]

        pipeline = MarketAlertPipeline(storage_file=self.random_storage_path)

        with patch('requests.get') as mock_requests_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(random_bytes)
            mock_requests_get.return_value = mock_response

            with patch.object(pipeline.storage, 'fetch_and_store') as mock_fetch_store:
                results = pipeline.run_batch_pipeline([self.random_url])

                self.assertIn(self.random_symbol, [r.get('symbol') for r in results])
                mock_fetch_store.assert_called()