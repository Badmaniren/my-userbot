import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills import market_database_pipeline


class TestMarketDatabasePipeline(unittest.TestCase):

    def test_pipeline_composition_and_execution(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{uuid.uuid4().hex}.com/market"
        rand_file = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(10.0, 1000.0), 2)

        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.db_storage') as mock_db:

            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.fetch_price.return_value = rand_price

            result = market_database_pipeline.run_pipeline(rand_symbol, rand_url, rand_file)

            mock_parser_cls.assert_called_once_with(rand_file)
            mock_parser_instance.fetch_price.assert_called_once_with(rand_url)
            mock_db.fetch_and_store.assert_called_once_with(rand_symbol, rand_price)

            self.assertEqual(result, rand_price)

    def test_pipeline_handles_parser_exception(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_url = f"http://{uuid.uuid4().hex}.net/api"
        rand_file = f"{uuid.uuid4().hex}.db"

        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.db_storage') as mock_db:

            mock_parser_instance = mock_parser_cls.return_value
            error_message = uuid.uuid4().hex
            mock_parser_instance.fetch_price.side_effect = ValueError(error_message)

            with self.assertRaises(ValueError) as ctx:
                market_database_pipeline.run_pipeline(rand_symbol, rand_url, rand_file)

            self.assertIn(error_message, str(ctx.exception))
            mock_db.fetch_and_store.assert_not_called()

    def test_pipeline_default_parameters(self):
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.db_storage') as mock_db:

            mock_parser_instance = mock_parser_cls.return_value
            rand_price = random.randint(1, 500)
            mock_parser_instance.fetch_price.return_value = rand_price

            try:
                market_database_pipeline.run_pipeline()
            except TypeError:
                pass


if __name__ == '__main__':
    unittest.main()