import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string

from skills.market_database_pipeline import run_market_database_pipeline


class TestMarketDatabasePipeline(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/market"
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

    def test_pipeline_success(self):
        with patch('skills.market_database_pipeline.market_parser') as mock_parser, \
             patch('skills.market_database_pipeline.db_storage') as mock_storage:

            mock_parser.fetch_price.return_value = self.random_price

            run_market_database_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                storage_file=self.random_storage
            )

            mock_parser.fetch_price.assert_called_once_with(self.random_url)
            mock_storage.fetch_and_store.assert_called_once_with(
                self.random_storage, self.random_symbol, self.random_price
            )

    def test_pipeline_parser_exception_propagates(self):
        with patch('skills.market_database_pipeline.market_parser') as mock_parser, \
             patch('skills.market_database_pipeline.db_storage') as mock_storage:

            random_error_message = uuid.uuid4().hex
            mock_parser.fetch_price.side_effect = ValueError(random_error_message)

            with self.assertRaises(ValueError) as ctx:
                run_market_database_pipeline(
                    symbol=self.random_symbol,
                    url=self.random_url,
                    storage_file=self.random_storage
                )

            self.assertEqual(str(ctx.exception), random_error_message)
            mock_storage.fetch_and_store.assert_not_called()

    def test_pipeline_storage_exception_propagates(self):
        with patch('skills.market_database_pipeline.market_parser') as mock_parser, \
             patch('skills.market_database_pipeline.db_storage') as mock_storage:

            mock_parser.fetch_price.return_value = self.random_price
            random_error_message = uuid.uuid4().hex
            mock_storage.fetch_and_store.side_effect = RuntimeError(random_error_message)

            with self.assertRaises(RuntimeError) as ctx:
                run_market_database_pipeline(
                    symbol=self.random_symbol,
                    url=self.random_url,
                    storage_file=self.random_storage
                )

            self.assertEqual(str(ctx.exception), random_error_message)
            mock_parser.fetch_price.assert_called_once_with(self.random_url)
            mock_storage.fetch_and_store.assert_called_once()


if __name__ == '__main__':
    unittest.main()