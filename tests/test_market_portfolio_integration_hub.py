import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub


class TestMarketPortfolioIntegrationHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.hub = MarketPortfolioIntegrationHub(storage_file=self.storage_file)

    def test_init_attributes(self):
        self.assertEqual(self.hub.storage_file, self.storage_file)
        self.assertIsNotNone(self.hub.gateway)
        self.assertIsNotNone(self.hub.exporter)
        self.assertEqual(self.hub.api_gateway, self.hub.gateway)
        self.assertEqual(self.hub.data_exporter, self.hub.exporter)

    def test_run_integrated_pipeline_success(self):
        url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        shifts = random.randint(1, 100)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 999999))

        with patch.object(self.hub.gateway, 'export_portfolio_summary') as mock_summary, \
             patch.object(self.hub.exporter, 'export_all') as mock_export:
            
            mock_summary.return_value = {uuid.uuid4().hex: random.randint(1, 500)}
            mock_export.return_value = [uuid.uuid4().hex, random.randint(10, 50)]

            result = self.hub.run_integrated_pipeline(url, symbol, shifts, telegram_token, chat_id)
            
            self.assertTrue(result)
            mock_summary.assert_called_once_with(url)
            mock_export.assert_called_once_with(url, symbol, shifts)

    def test_run_integrated_pipeline_failure(self):
        url = f"https://{uuid.uuid4().hex}.net/{uuid.uuid4().hex}"
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        shifts = random.randint(1, 50)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100, 999))

        with patch.object(self.hub.gateway, 'export_portfolio_summary', side_effect=Exception(uuid.uuid4().hex)):
            result = self.hub.run_integrated_pipeline(url, symbol, shifts, telegram_token, chat_id)
            self.assertFalse(result)

    def test_export_and_dispatch_stream(self):
        expected_stream = [uuid.uuid4().hex, random.randint(100, 999)]

        with patch.object(self.hub.exporter, 'export_stream', return_value=expected_stream) as mock_stream:
            result = self.hub.export_and_dispatch_stream()
            
            self.assertEqual(result, expected_stream)
            mock_stream.assert_called_once()

    def test_execute_custom_export(self):
        url = f"https://{uuid.uuid4().hex}.org/{uuid.uuid4().hex}"
        shifts = random.randint(5, 50)
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.exporter, 'export_data', return_value=expected_data) as mock_data:
            result = self.hub.execute_custom_export(url, shifts)
            
            self.assertEqual(result, expected_data)
            mock_data.assert_called_once_with(url, shifts)

    def test_process_and_export(self):
        url = f"https://{uuid.uuid4().hex}.io/{uuid.uuid4().hex}"
        symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        shifts = random.randint(1, 10)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))

        summary_data = {uuid.uuid4().hex: random.random()}
        export_results = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch.object(self.hub.gateway, 'export_portfolio_summary', return_value=summary_data) as mock_summary, \
             patch.object(self.hub.exporter, 'export_all', return_value=export_results) as mock_export:
            
            result = self.hub.process_and_export(url, symbol, shifts, telegram_token, chat_id)
            
            self.assertIsInstance(result, dict)
            self.assertIn("summary", result)
            self.assertIn("export_data", result)
            self.assertEqual(result["summary"], summary_data)
            self.assertEqual(result["export_data"], export_results)
            
            mock_summary.assert_called_once_with(url)
            mock_export.assert_called_once_with(url, symbol, shifts)

    def test_run_full_integration_pipeline(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=6))
        url = f"https://{uuid.uuid4().hex}.biz/{uuid.uuid4().hex}"
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))
        shifts = random.randint(2, 20)

        with patch.object(self.hub, 'process_and_export') as mock_process:
            mock_return_val = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_process.return_value = mock_return_val

            result = self.hub.run_full_integration_pipeline(symbol, url, telegram_token, chat_id, shifts)

            self.assertEqual(result, mock_return_val)
            mock_process.assert_called_once_with(url, symbol, shifts, telegram_token, chat_id)


if __name__ == '__main__':
    unittest.main()