import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_export_pipeline import MarketExportPipeline

class TestMarketExportPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.pipeline = MarketExportPipeline(self.storage_file)

    @patch('skills.market_export_pipeline.MarketParser')
    @patch('skills.market_export_pipeline.MarketReportGenerator')
    def test_export_aggregated_stream(self, mock_report_gen_cls, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value
        mock_report_gen = mock_report_gen_cls.return_value

        expected_dump = f"stream_{uuid.uuid4().hex}"
        mock_report_gen.get_raw_stream_dump.return_value = expected_dump

        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        url = f"https://example.com/{uuid.uuid4().hex}"

        pipeline = MarketExportPipeline(self.storage_file)
        result = pipeline.export_aggregated_stream(symbol, url)

        mock_parser.fetch_and_store.assert_called_once_with(url, symbol)
        mock_report_gen.update_and_fetch_report.assert_called_once_with(url, symbol)
        mock_report_gen.get_raw_stream_dump.assert_called_once()
        self.assertEqual(result, expected_dump)

    @patch('skills.market_export_pipeline.MarketParser')
    def test_export_historical_data(self, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value
        expected_data = {"data": uuid.uuid4().hex}
        mock_parser.load_data.return_value = expected_data

        filename = f"{uuid.uuid4().hex}.csv"
        pipeline = MarketExportPipeline(self.storage_file)
        result = pipeline.export_historical_data(filename)

        mock_parser.load_data.assert_called_once_with(filename)
        self.assertEqual(result, expected_data)

    @patch('skills.market_export_pipeline.MarketReportGenerator')
    def test_export_symbol_report(self, mock_report_gen_cls):
        mock_report_gen = mock_report_gen_cls.return_value
        expected_report = {"report_id": uuid.uuid4().hex}
        mock_report_gen.generate_symbol_report.return_value = expected_report

        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        pipeline = MarketExportPipeline(self.storage_file)
        result = pipeline.export_symbol_report(symbol)

        mock_report_gen.generate_symbol_report.assert_called_once_with(symbol)
        self.assertEqual(result, expected_report)

    @patch('skills.market_export_pipeline.MarketParser')
    def test_export_aggregated_data(self, mock_parser_cls):
        mock_parser = mock_parser_cls.return_value

        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(10.0, 1000.0), 2)
        url = f"https://example.com/{uuid.uuid4().hex}"
        export_id = uuid.uuid4().hex

        pipeline = MarketExportPipeline(self.storage_file)

        with patch.object(pipeline, 'db_storage') as mock_db:
            result = pipeline.export_aggregated_data(symbol, price, url, export_id)

            mock_parser.fetch_and_store.assert_called_once_with(url, symbol)
            mock_db.save_data.assert_called_once()

            saved_arg = mock_db.save_data.call_args[0][1]
            self.assertEqual(len(saved_arg), 1)
            self.assertEqual(saved_arg[0]["export_id"], export_id)
            self.assertEqual(saved_arg[0]["symbol"], symbol)
            self.assertEqual(saved_arg[0]["price"], price)
            self.assertEqual(saved_arg[0]["url"], url)

            self.assertIn(export_id, result)
            self.assertIn(symbol, result)

if __name__ == '__main__':
    unittest.main()