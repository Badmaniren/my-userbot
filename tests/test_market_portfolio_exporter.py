import unittest
from unittest.mock import patch, mock_open, MagicMock
import io
import json
import csv
import random
import uuid
import string
from skills.market_portfolio_exporter import MarketPortfolioExporter

class TestMarketPortfolioExporter(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.exporter = MarketPortfolioExporter(self.random_storage)

    def test_export_to_json_success(self):
        mock_data = {
            uuid.uuid4().hex: random.uniform(10.0, 1000.0),
            uuid.uuid4().hex: random.uniform(1.0, 500.0)
        }
        random_filepath = f"{uuid.uuid4().hex}.json"

        with patch('skills.market_portfolio_exporter.MarketPortfolioExporter.load_data', return_value=mock_data), \
             patch('builtins.open', mock_open()) as mock_file:

            result = self.exporter.export_to_json(random_filepath)

            mock_file.assert_called_once_with(random_filepath, 'w', encoding='utf-8')
            handle = mock_file()

            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_content = json.loads(written_content)

            self.assertEqual(parsed_content, mock_data)
            self.assertTrue(result)

    def test_export_to_csv_success(self):
        random_symbol = uuid.uuid4().hex[:8]
        random_price = random.uniform(50.0, 5000.0)
        mock_data = {
            random_symbol: random_price
        }
        random_filepath = f"{uuid.uuid4().hex}.csv"

        with patch('skills.market_portfolio_exporter.MarketPortfolioExporter.load_data', return_value=mock_data), \
             patch('builtins.open', mock_open()) as mock_file:

            result = self.exporter.export_to_csv(random_filepath)

            mock_file.assert_called_once_with(random_filepath, 'w', newline='', encoding='utf-8')
            handle = mock_file()

            written_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(random_symbol, written_content)
            self.assertIn(str(random_price), written_content)
            self.assertTrue(result)

    def test_export_to_json_exception_handling(self):
        random_filepath = f"{uuid.uuid4().hex}.json"

        with patch('skills.market_portfolio_exporter.MarketPortfolioExporter.load_data', side_effect=Exception(uuid.uuid4().hex)), \
             patch('builtins.open', mock_open()) as mock_file:

            result = self.exporter.export_to_json(random_filepath)

            self.assertFalse(result)

    def test_export_to_csv_exception_handling(self):
        random_filepath = f"{uuid.uuid4().hex}.csv"

        with patch('skills.market_portfolio_exporter.MarketPortfolioExporter.load_data', side_effect=Exception(uuid.uuid4().hex)), \
             patch('builtins.open', mock_open()) as mock_file:

            result = self.exporter.export_to_csv(random_filepath)

            self.assertFalse(result)

    def test_load_data_valid_json(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(100, 999)
        mock_file_content = json.dumps({random_key: random_val})

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_file_content)):

            data = self.exporter.load_data(self.random_storage)
            self.assertEqual(data.get(random_key), random_val)

    def test_load_data_file_not_exists(self):
        with patch('os.path.exists', return_value=False):
            data = self.exporter.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_load_data_corrupted_json(self):
        random_garbage = "".join(random.choices(string.ascii_letters, k=15))

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=random_garbage)):

            data = self.exporter.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_get_export_stream_dump(self):
        mock_data = {
            uuid.uuid4().hex: random.uniform(1.0, 100.0)
        }

        with patch('skills.market_portfolio_exporter.MarketPortfolioExporter.load_data', return_value=mock_data):
            stream_dump = self.exporter.get_export_stream_dump()
            parsed_dump = json.loads(stream_dump)
            self.assertEqual(parsed_dump, mock_data)

    def test_verify_stream_integrity_bytes(self):
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        result = self.exporter.verify_stream_integrity(mock_stream)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()