import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_data_exporter import PortfolioDataExporter, export_portfolio_data_pipeline

class TestPortfolioDataExporter(unittest.TestCase):

    def setUp(self):
        self.storage_path = f"/tmp/{uuid.uuid4().hex}.db"
        self.exporter = PortfolioDataExporter(self.storage_path)

    def test_export_all_integrity(self):
        random_url = f"https://{uuid.uuid4().hex}.com/api"
        random_symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        random_shifts = [random.uniform(-1.0, 1.0) for _ in range(3)]
        
        expected_summary = {"token_ref": uuid.uuid4().hex, "data": random.random()}
        expected_stress = {"volatility": random.random(), "id": uuid.uuid4().hex}

        with patch('skills.market_portfolio_api_gateway.MarketPortfolioAPIGateway.export_portfolio_summary') as mock_gateway:
            with patch('skills.market_portfolio_stress_reporter.StressReporter.run_stress_reporting') as mock_reporter:
                mock_gateway.return_value = expected_summary
                mock_reporter.return_value = expected_stress
                
                result = self.exporter.export_all(random_url, random_symbol, random_shifts)
                
                self.assertEqual(result["portfolio_summary"], expected_summary)
                self.assertEqual(result["stress_report"], expected_stress)
                mock_gateway.assert_called_once_with(random_url)
                mock_reporter.assert_called_once_with(random_symbol, random_shifts)

    def test_export_stream_data_type(self):
        random_bytes = uuid.uuid4().bytes
        
        with patch('skills.market_portfolio_stress_reporter.StressReporter.get_stream_data') as mock_stream:
            mock_stream.return_value = io.BytesIO(random_bytes)
            
            stream = self.exporter.export_stream()
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read(), random_bytes)

    def test_pipeline_execution_flow(self):
        random_storage = f"{uuid.uuid4().hex}.db"
        random_url = f"https://{uuid.uuid4().hex}.io"
        random_symbol = uuid.uuid4().hex[:5]
        random_shifts = [random.randint(1, 100)]
        random_token = uuid.uuid4().hex
        random_chat = str(random.randint(1000, 9999))
        random_template = uuid.uuid4().hex
        random_ref = uuid.uuid4().hex

        with patch('skills.market_portfolio_data_exporter.PortfolioDataExporter.export_all') as mock_export:
            with patch('skills.market_portfolio_data_exporter.send_telegram_notification') as mock_notify:
                mock_export.return_value = {"portfolio_summary": {"token_ref": random_ref}}
                mock_notify.return_value = True
                
                status = export_portfolio_data_pipeline(
                    random_storage, random_url, random_symbol, 
                    random_shifts, random_token, random_chat, random_template
                )
                
                self.assertTrue(status)
                expected_msg = f"{random_template} - Symbol: {random_symbol} - Export ID: {random_ref}"
                mock_notify.assert_called_once_with(random_token, random_chat, expected_msg)

    def test_export_data_gateway_passthrough(self):
        random_url = f"https://{uuid.uuid4().hex}.net"
        random_shifts = []
        expected_data = {"status": uuid.uuid4().hex}
        
        with patch('skills.market_portfolio_api_gateway.MarketPortfolioAPIGateway.export_portfolio_summary') as mock_gateway:
            mock_gateway.return_value = expected_data
            result = self.exporter.export_data(random_url, random_shifts)
            
            self.assertEqual(result, expected_data)
            mock_gateway.assert_called_once_with(random_url)

if __name__ == '__main__':
    unittest.main()