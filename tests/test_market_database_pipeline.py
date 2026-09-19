import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_database_pipeline import MarketDatabasePipeline

class TestMarketDatabasePipeline(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_db_{self.rand_suffix}.dat"
        self.pipeline = MarketDatabasePipeline(storage_file=self.storage_file)

    def test_pipeline_composition_and_storage(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        rand_price = round(random.uniform(10.0, 1000.0), 2)

        with patch.object(self.pipeline.storage, 'fetch_and_store') as mock_store:
            result = self.pipeline.run_pipeline(symbol=rand_symbol, price=rand_price)
            self.assertTrue(result)
            mock_store.assert_called_once_with(rand_symbol, rand_price)

    def test_pipeline_fetch_and_store_flow(self):
        rand_url = f"https://example.com/market/{uuid.uuid4().hex}"
        rand_symbol = f"COIN_{uuid.uuid4().hex[:4].upper()}"
        rand_price = round(random.uniform(1.0, 500.0), 2)

        with patch.object(self.pipeline.parser, 'fetch_price', return_value=rand_price) as mock_fetch, \
             patch.object(self.pipeline.storage, 'fetch_and_store') as mock_store:

            res = self.pipeline.run_pipeline(url=rand_url, symbol=rand_symbol)

            mock_fetch.assert_called_once_with(rand_url)
            mock_store.assert_called_once_with(rand_symbol, rand_price)
            self.assertEqual(res, rand_price)

    def test_get_stored_data_handles_unicode_decode_error(self):
        rand_filename = f"corrupted_{uuid.uuid4().hex}.bin"

        with patch.object(self.pipeline.storage, 'load_data', side_effect=UnicodeDecodeError('utf-8', b'\x89', 99, 100, 'invalid start byte')) as mock_load:
            data = self.pipeline.get_stored_data(rand_filename)
            mock_load.assert_called_once_with(rand_filename)
            self.assertEqual(data, [])

    def test_get_stored_data_success(self):
        rand_filename = f"valid_{uuid.uuid4().hex}.dat"
        rand_line = f"record_{uuid.uuid4().hex}"

        with patch.object(self.pipeline.storage, 'load_data', return_value=[rand_line]) as mock_load:
            data = self.pipeline.get_stored_data(rand_filename)
            mock_load.assert_called_once_with(rand_filename)
            self.assertEqual(data, [rand_line])

    def test_process_html_stream_delegation(self):
        rand_url = f"https://market-feed.net/{uuid.uuid4().hex}"
        rand_prices = [round(random.uniform(10, 50), 2), round(random.uniform(51, 100), 2)]

        with patch.object(self.pipeline.parser, 'parse_html_prices', return_value=rand_prices) as mock_parse:
            result = self.pipeline.process_html_stream(rand_url)
            mock_parse.assert_called_once_with(rand_url)
            self.assertEqual(result, rand_prices)

if __name__ == '__main__':
    unittest.main()