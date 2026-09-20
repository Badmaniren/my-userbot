import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json

from skills.market_portfolio_data_exporter import (
    PortfolioDataExporter,
    export_portfolio_data_pipeline
)

class TestMarketPortfolioDataExporter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.url = f"https://api.{uuid.uuid4().hex}.com/v1/export"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        self.shifts = [random.uniform(-10.0, 10.0), random.uniform(-20.0, 20.0)]
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.expected_export_id = uuid.uuid4().hex
        self.expected_stress_data = {
            uuid.uuid4().hex: random.uniform(100, 5000),
            uuid.uuid4().hex: random.uniform(-500, 500)
        }

    def test_exporter_initialization(self):
        with patch('skills.market_portfolio_data_exporter.MarketPortfolioAPIGateway') as mock_gateway, \
             patch('skills.market_portfolio_data_exporter.StressReporter') as mock_reporter:
            
            exporter = PortfolioDataExporter(self.storage_file)
            
            mock_gateway.assert_called_once_with(self.storage_file)
            mock_reporter.assert_called_once_with(self.storage_file)
            self.assertEqual(exporter.storage_file, self.storage_file)

    def test_export_portfolio_and_stress_success(self):
        with patch('skills.market_portfolio_data_exporter.MarketPortfolioAPIGateway') as MockGateway, \
             patch('skills.market_portfolio_data_exporter.StressReporter') as MockReporter:
            
            gateway_instance = MockGateway.return_value
            gateway_instance.export_portfolio_summary.return_value = {
                "status": "success",
                "export_id": self.expected_export_id,
                "symbol": self.symbol
            }

            reporter_instance = MockReporter.return_value
            reporter_instance.run_stress_reporting.return_value = self.expected_stress_data

            exporter = PortfolioDataExporter(self.storage_file)
            result = exporter.export_all(self.url, self.symbol, self.shifts)

            gateway_instance.export_portfolio_summary.assert_called_once_with(self.url)
            reporter_instance.run_stress_reporting.assert_called_once_with(self.symbol, self.shifts)

            self.assertIn("portfolio_summary", result)
            self.assertIn("stress_report", result)
            self.assertEqual(result["portfolio_summary"]["export_id"], self.expected_export_id)
            self.assertEqual(result["stress_report"], self.expected_stress_data)

    def test_export_pipeline_execution(self):
        with patch('skills.market_portfolio_data_exporter.MarketPortfolioAPIGateway') as MockGateway, \
             patch('skills.market_portfolio_data_exporter.StressReporter') as MockReporter, \
             patch('skills.market_portfolio_data_exporter.send_telegram_notification') as mock_notify:
            
            gateway_instance = MockGateway.return_value
            gateway_instance.export_portfolio_summary.return_value = {
                "status": "exported",
                "token_ref": uuid.uuid4().hex
            }

            reporter_instance = MockReporter.return_value
            reporter_instance.run_stress_reporting.return_value = self.expected_stress_data

            message_fragment = uuid.uuid4().hex

            result = export_portfolio_data_pipeline(
                storage_file=self.storage_file,
                url=self.url,
                symbol=self.symbol,
                shifts=self.shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                notification_template=message_fragment
            )

            mock_notify.assert_called_once()
            args, _ = mock_notify.call_args
            self.assertEqual(args[0], self.telegram_token)
            self.assertEqual(args[1], self.chat_id)
            self.assertIn(message_fragment, args[2])
            self.assertIn(self.symbol, args[2])
            self.assertTrue(result)

    def test_export_exception_handling(self):
        with patch('skills.market_portfolio_data_exporter.MarketPortfolioAPIGateway') as MockGateway, \
             patch('skills.market_portfolio_data_exporter.StressReporter') as MockReporter, \
             patch('skills.market_portfolio_data_exporter.send_telegram_notification') as mock_notify:
            
            gateway_instance = MockGateway.return_value
            error_msg = f"API_FAIL_{uuid.uuid4().hex}"
            gateway_instance.export_portfolio_summary.side_effect = Exception(error_msg)

            exporter = PortfolioDataExporter(self.storage_file)
            
            with self.assertRaises(Exception) as ctx:
                exporter.export_all(self.url, self.symbol, self.shifts)
            
            self.assertIn(error_msg, str(ctx.exception))

    def test_stream_data_export(self):
        with patch('skills.market_portfolio_data_exporter.MarketPortfolioAPIGateway') as MockGateway, \
             patch('skills.market_portfolio_data_exporter.StressReporter') as MockReporter:
            
            reporter_instance = MockReporter.return_value
            stream_dump = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
            reporter_instance.get_stream_data.return_value = stream_dump

            exporter = PortfolioDataExporter(self.storage_file)
            stream_result = exporter.export_stream()

            reporter_instance.get_stream_data.assert_called_once()
            self.assertEqual(stream_result.read().decode('utf-8'), stream_dump.getvalue().decode('utf-8'))

if __name__ == '__main__':
    unittest.main()