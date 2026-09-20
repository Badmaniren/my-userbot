import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_report_generator import MarketReportGenerator


class TestMarketReportGeneratorInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{random.randint(100, 999)}"
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_error_msg = uuid.uuid4().hex

    def test_composition_and_initialization(self):
        with patch('skills.market_report_generator.MarketParser') as mock_parser_cls, \
             patch('skills.market_report_generator.db_storage') as mock_db:
            
            mock_parser_instance = mock_parser_cls.return_value
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            
            mock_parser_cls.assert_called_once_with(self.random_storage)
            self.assertEqual(generator.parser, mock_parser_instance)
            self.assertEqual(generator.db, mock_db)

    def test_generate_report_success(self):
        raw_data = [
            {"symbol": self.random_symbol, "price": self.random_price, "id": uuid.uuid4().hex},
            {"symbol": self.random_symbol, "price": self.random_price + 50.0, "id": uuid.uuid4().hex}
        ]
        
        with patch('skills.market_report_generator.MarketParser') as mock_parser_cls, \
             patch('skills.market_report_generator.db_storage') as mock_db:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = raw_data
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            report = generator.generate_symbol_report(self.random_symbol)
            
            mock_parser_instance.load_data.assert_called_once_with(self.random_storage)
            self.assertIn(self.random_symbol, report)
            self.assertEqual(report['count'], 2)
            self.assertEqual(report['min_price'], self.random_price)
            self.assertEqual(report['max_price'], self.random_price + 50.0)

    def test_generate_report_empty_data(self):
        with patch('skills.market_report_generator.MarketParser') as mock_parser_cls, \
             patch('skills.market_report_generator.db_storage'):
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = []
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            report = generator.generate_symbol_report(self.random_symbol)
            
            self.assertEqual(report['count'], 0)
            self.assertIn('error', report)

    def test_fetch_and_generate_pipeline(self):
        with patch('skills.market_report_generator.MarketParser') as mock_parser_cls, \
             patch('skills.market_report_generator.db_storage') as mock_db:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.fetch_price.return_value = self.random_price
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            price = generator.update_and_fetch_report(self.random_url, self.random_symbol)
            
            mock_parser_instance.fetch_price.assert_called_once_with(self.random_url)
            mock_parser_instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)
            self.assertEqual(price, self.random_price)

    def test_io_stream_handling_in_report(self):
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)
        
        with patch('skills.market_report_generator.MarketParser') as mock_parser_cls, \
             patch('skills.market_report_generator.db_storage'):
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = [{"stream_data": mock_stream.read()}]
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            data = generator.get_raw_stream_dump()
            
            self.assertEqual(data[0]["stream_data"], random_bytes)


if __name__ == '__main__':
    unittest.main()