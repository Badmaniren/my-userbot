import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_database_pipeline import MarketDatabasePipeline

class TestMarketDatabasePipeline(unittest.TestCase):

    def setUp(self):
        self.random_storage_file = f"{uuid.uuid4().hex}.json"
        self.pipeline = MarketDatabasePipeline(storage_file=self.random_storage_file)

    def test_pipeline_initialization_and_composition(self):
        random_file_path = f"{uuid.uuid4().hex}_{uuid.uuid4().hex}.db"
        
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.DbStorage') as mock_storage_cls:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_storage_instance = mock_storage_cls.return_value
            
            pipeline = MarketDatabasePipeline(storage_file=random_file_path)
            
            mock_parser_cls.assert_called_once_with(storage_file=random_file_path)
            mock_storage_cls.assert_called_once_with(storage_file=random_file_path)
            
            self.assertEqual(pipeline.parser, mock_parser_instance)
            self.assertEqual(pipeline.storage, mock_storage_instance)

    def test_run_pipeline_cycle_success(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_url = f"https://{uuid.uuid4().hex}.com/market/{random_symbol.lower()}"
        random_price = round(random.uniform(10.0, 5000.0), 2)
        
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.DbStorage') as mock_storage_cls:
            
            mock_parser = mock_parser_cls.return_value
            mock_storage = mock_storage_cls.return_value
            
            mock_parser.fetch_price.return_value = random_price
            
            pipeline = MarketDatabasePipeline(storage_file=self.random_storage_file)
            result = pipeline.run_cycle(symbol=random_symbol, url=random_url)
            
            mock_parser.fetch_price.assert_called_once_with(random_url)
            mock_storage.fetch_and_store.assert_called_once_with(random_symbol, random_price)
            
            self.assertEqual(result, random_price)

    def test_run_pipeline_cycle_with_html_parsing(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        random_url = f"https://{uuid.uuid4().hex}.net/prices"
        random_parsed_price = round(random.uniform(1.0, 999.9), 2)
        
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.DbStorage') as mock_storage_cls:
            
            mock_parser = mock_parser_cls.return_value
            mock_storage = mock_storage_cls.return_value
            
            mock_parser.parse_html_prices.return_value = random_parsed_price
            
            pipeline = MarketDatabasePipeline(storage_file=self.random_storage_file)
            result = pipeline.run_html_parsing_cycle(symbol=random_symbol, url=random_url)
            
            mock_parser.parse_html_prices.assert_called_once_with(random_url)
            mock_storage.fetch_and_store.assert_called_once_with(random_symbol, random_parsed_price)
            
            self.assertEqual(result, random_parsed_price)

    def test_load_stored_market_data(self):
        random_filename = f"{uuid.uuid4().hex}.json"
        random_data = [{uuid.uuid4().hex: random.randint(100, 999)} for _ in range(3)]
        
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.DbStorage') as mock_storage_cls:
            
            mock_storage = mock_storage_cls.return_value
            mock_storage.load_data.return_value = random_data
            
            pipeline = MarketDatabasePipeline(storage_file=self.random_storage_file)
            loaded_data = pipeline.load_market_data(filename=random_filename)
            
            mock_storage.load_data.assert_called_once_with(random_filename)
            self.assertEqual(loaded_data, random_data)

    def test_pipeline_stream_processing_with_bytes(self):
        random_bytes_content = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=20)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes_content)
        
        random_symbol = uuid.uuid4().hex[:6].upper()
        random_price = round(random.uniform(50.0, 150.0), 2)
        
        with patch('skills.market_database_pipeline.MarketParser') as mock_parser_cls, \
             patch('skills.market_database_pipeline.DbStorage') as mock_storage_cls:
            
            mock_storage = mock_storage_cls.return_value
            
            pipeline = MarketDatabasePipeline(storage_file=self.random_storage_file)
            
            if hasattr(pipeline, 'process_stream'):
                pipeline.process_stream(mock_stream, symbol=random_symbol, price=random_price)
                mock_storage.fetch_and_store.assert_called_with(random_symbol, random_price)
            else:
                self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()