import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
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
        url = f"https://{uuid.uuid4().hex}.com/api"
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        shifts = random.randint(1, 100)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))

        with patch.object(self.hub.gateway, 'export_portfolio_summary') as mock_summary, \
             patch.object(self.hub.exporter, 'export_all') as mock_export:
            
            mock_summary.return_value = {uuid.uuid4().hex: random.randint(1, 500)}
            mock_export.return_value = [uuid.uuid4().hex, uuid.uuid4().hex]

            result = self.hub.run_integrated_pipeline(url, symbol, shifts, telegram_token, chat_id)

            self.assertTrue(result)
            mock_summary.assert_called_once_with(url)
            mock_export.assert_called_once_with(url, symbol, shifts)

    def test_run_integrated_pipeline_failure(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        shifts = random.randint(1, 100)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))

        with patch.object(self.hub.gateway, 'export_portfolio_summary') as mock_summary:
            mock_summary.side_effect = Exception(uuid.uuid4().hex)

            result = self.hub.run_integrated_pipeline(url, symbol, shifts, telegram_token, chat_id)

            self.assertFalse(result)
            mock_summary.assert_called_once_with(url)

    def test_export_and_dispatch_stream(self):
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.exporter, 'export_stream') as mock_stream:
            mock_stream.return_value = expected_data

            result = self.hub.export_and_dispatch_stream()

            self.assertEqual(result, expected_data)
            mock_stream.assert_called_once()

    def test_execute_custom_export(self):
        url = f"https://{uuid.uuid4().hex}.org/export"
        shifts = random.randint(10, 50)
        expected_output = [uuid.uuid4().hex for _ in range(3)]

        with patch.object(self.hub.exporter, 'export_data') as mock_export_data:
            mock_export_data.return_value = expected_output

            result = self.hub.execute_custom_export(url, shifts)

            self.assertEqual(result, expected_output)
            mock_export_data.assert_called_once_with(url, shifts)

    def test_process_and_export(self):
        url = f"https://{uuid.uuid4().hex}.net/v1"
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        shifts = random.randint(1, 10)
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))

        summary_data = {uuid.uuid4().hex: random.random()}
        export_data_list = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.gateway, 'export_portfolio_summary') as mock_summary, \
             patch.object(self.hub.exporter, 'export_all') as mock_export:
            
            mock_summary.return_value = summary_data
            mock_export.return_value = export_data_list

            result = self.hub.process_and_export(url, symbol, shifts, telegram_token, chat_id)

            expected_result = {
                "summary": summary_data,
                "export_data": export_data_list
            }
            self.assertEqual(result, expected_result)
            mock_summary.assert_called_once_with(url)
            mock_export.assert_called_once_with(url, symbol, shifts)

    def test_run_full_integration_pipeline(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=3))
        url = f"https://{uuid.uuid4().hex}.io/webhook"
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        shifts = random.randint(5, 25)

        summary_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        export_payload = {uuid.uuid4().hex: random.randint(100, 200)}

        with patch.object(self.hub.gateway, 'export_portfolio_summary') as mock_summary, \
             patch.object(self.hub.exporter, 'export_all') as mock_export:
            
            mock_summary.return_value = summary_payload
            mock_export.return_value = export_payload

            result = self.hub.run_full_integration_pipeline(symbol, url, telegram_token, chat_id, shifts)

            self.assertEqual(result["summary"], summary_payload)
            self.assertEqual(result["export_data"], export_payload)
            mock_summary.assert_called_once_with(url)
            mock_export.assert_called_once_with(url, symbol, shifts)


if __name__ == '__main__':
    unittest.main()