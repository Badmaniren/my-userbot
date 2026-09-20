import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.market_portfolio_visualizer_v2 import (
    PortfolioVisualizer,
    generate_ascii_chart,
    format_pnl_notification
)

class TestMarketPortfolioVisualizerV2(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_file = f"{uuid.uuid4().hex}.json"
        self.rand_url = f"https://{uuid.uuid4().hex}.com/api"

    def test_ascii_chart_generation_random_data(self):
        data_points = [round(random.uniform(10.0, 1000.0), 2) for _ in range(random.randint(5, 15))]
        chart = generate_ascii_chart(data_points)
        
        self.assertIsInstance(chart, str)
        self.assertGreater(len(chart), 0)
        for point in data_points:
            self.assertIn(str(int(point))[:3], chart)

    def test_ascii_chart_empty_data(self):
        chart = generate_ascii_chart([])
        self.assertEqual(chart, "[No Data Available]")

    def test_portfolio_visualizer_initialization(self):
        visualizer = PortfolioVisualizer(self.rand_file)
        self.assertEqual(visualizer.storage_file, self.rand_file)

    def test_visualizer_build_text_report(self):
        visualizer = PortfolioVisualizer(self.rand_file)
        
        mock_data = [
            {"timestamp": uuid.uuid4().hex, "price": random.uniform(100, 200)}
            for _ in range(5)
        ]
        
        with patch.object(visualizer, 'load_data', return_value=mock_data):
            report = visualizer.build_text_report(self.rand_symbol)
            self.assertIsInstance(report, str)
            self.assertIn(self.rand_symbol, report)
            self.assertIn("PnL", report)

    def test_format_pnl_notification_positive(self):
        pnl_value = round(random.uniform(10.5, 500.0), 2)
        percentage = round(random.uniform(1.0, 50.0), 2)
        
        message = format_pnl_notification(self.rand_symbol, pnl_value, percentage)
        
        self.assertIsInstance(message, str)
        self.assertIn(self.rand_symbol, message)
        self.assertIn(str(pnl_value), message)
        self.assertIn("🟢", message)

    def test_format_pnl_notification_negative(self):
        pnl_value = -round(random.uniform(10.5, 500.0), 2)
        percentage = -round(random.uniform(1.0, 50.0), 2)
        
        message = format_pnl_notification(self.rand_symbol, pnl_value, percentage)
        
        self.assertIsInstance(message, str)
        self.assertIn(self.rand_symbol, message)
        self.assertIn(str(pnl_value), message)
        self.assertIn("🔴", message)

    def test_visualizer_load_data_stream(self):
        visualizer = PortfolioVisualizer(self.rand_file)
        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)
        
        with patch('builtins.open', return_value=mock_stream):
            data = visualizer.load_data(self.rand_file)
            self.assertIsNotNone(data)

    def test_visualizer_render_and_dispatch_flow(self):
        visualizer = PortfolioVisualizer(self.rand_file)
        mock_token = uuid.uuid4().hex
        mock_chat_id = str(random.randint(100000, 999999))
        
        with patch('skills.market_portfolio_visualizer_v2.send_telegram_notification') as mock_send:
            with patch.object(visualizer, 'build_text_report', return_value=f"Report {uuid.uuid4().hex}"):
                visualizer.render_and_dispatch(self.rand_symbol, mock_token, mock_chat_id)
                mock_send.assert_called_once()
                args, _ = mock_send.call_args
                self.assertEqual(args[0], mock_token)
                self.assertEqual(args[1], mock_chat_id)

if __name__ == '__main__':
    unittest.main()