import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioIntegrationHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.url = f"https://{uuid.uuid4().hex}.com/market"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(-999999999, -100000000))
        self.shifts = random.randint(1, 30)
        self.notification_template = f"Report: {uuid.uuid4().hex}"

    def test_hub_composition_and_initialization(self):
        rand_storage = f"db_{uuid.uuid4().hex}.json"
        hub = MarketPortfolioIntegrationHub(rand_storage)
        self.assertEqual(hub.storage_file, rand_storage)
        self.assertIsNotNone(hub.gateway)
        self.assertIsNotNone(hub.exporter)

    @patch('skills.market_portfolio_integration_hub.MarketPortfolioAPIGateway')
    @patch('skills.market_portfolio_integration_hub.PortfolioDataExporter')
    def test_run_integrated_pipeline_success(self, mock_exporter_cls, mock_gateway_cls):
        mock_gateway = mock_gateway_cls.return_value
        mock_exporter = mock_exporter_cls.return_value

        expected_summary = {uuid.uuid4().hex: random.randint(100, 500)}
        mock_gateway.export_portfolio_summary.return_value = expected_summary
        mock_exporter.export_all.return_value = expected_summary

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        result = hub.run_integrated_pipeline(
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        mock_gateway.export_portfolio_summary.assert_called_once_with(self.url)
        mock_exporter.export_all.assert_called_once_with(self.url, self.symbol, self.shifts)
        self.assertTrue(result)

    @patch('skills.market_portfolio_integration_hub.MarketPortfolioAPIGateway')
    @patch('skills.market_portfolio_integration_hub.PortfolioDataExporter')
    def test_run_integrated_pipeline_exception_handling(self, mock_exporter_cls, mock_gateway_cls):
        mock_gateway = mock_gateway_cls.return_value
        mock_gateway.export_portfolio_summary.side_effect = Exception(uuid.uuid4().hex)

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        result = hub.run_integrated_pipeline(
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        self.assertFalse(result)

    @patch('skills.market_portfolio_integration_hub.MarketPortfolioAPIGateway')
    @patch('skills.market_portfolio_integration_hub.PortfolioDataExporter')
    def test_export_and_dispatch_stream(self, mock_exporter_cls, mock_gateway_cls):
        mock_exporter = mock_exporter_cls.return_value
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        mock_exporter.export_stream.return_value = io.BytesIO(random_bytes)

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        stream_data = hub.export_and_dispatch_stream()

        mock_exporter.export_stream.assert_called_once()
        self.assertIsInstance(stream_data, io.BytesIO)
        self.assertEqual(stream_data.read(), random_bytes)

    @patch('skills.market_portfolio_integration_hub.MarketPortfolioAPIGateway')
    @patch('skills.market_portfolio_integration_hub.PortfolioDataExporter')
    def test_execute_custom_export(self, mock_exporter_cls, mock_gateway_cls):
        mock_exporter = mock_exporter_cls.return_value
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_exporter.export_data.return_value = expected_dict

        hub = MarketPortfolioIntegrationHub(self.storage_file)
        res = hub.execute_custom_export(self.url, self.shifts)

        mock_exporter.export_data.assert_called_once_with(self.url, self.shifts)
        self.assertEqual(res, expected_dict)

if __name__ == '__main__':
    unittest.main()