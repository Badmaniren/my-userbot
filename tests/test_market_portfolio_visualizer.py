import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_visualizer import PortfolioVisualizer, generate_ascii_chart, render_text_trend

class TestMarketPortfolioVisualizer(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_load_data_non_existent(self):
        rand_path = f"{uuid.uuid4().hex}.json"
        visualizer = PortfolioVisualizer(rand_path)
        data = visualizer.load_data()
        self.assertEqual(data, [])

    def test_load_data_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")
        visualizer = PortfolioVisualizer(self.storage_file)
        data = visualizer.load_data()
        self.assertEqual(data, [])

    def test_load_data_unicode_error_handling(self):
        rand_bytes = bytes([random.randint(128, 255) for _ in range(32)])
        with open(self.storage_file, "wb") as f:
            f.write(rand_bytes)
        visualizer = PortfolioVisualizer(self.storage_file)
        data = visualizer.load_data()
        self.assertEqual(data, [])

    def test_load_data_list_format(self):
        symbol = uuid.uuid4().hex
        price = random.uniform(10.0, 1000.0)
        content = [{"symbol": symbol, "price": price}]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(content, f)
        visualizer = PortfolioVisualizer(self.storage_file)
        data = visualizer.load_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], symbol)
        self.assertEqual(data[0]["price"], price)

    def test_load_data_dict_format(self):
        symbol = uuid.uuid4().hex
        price = random.uniform(10.0, 1000.0)
        content = {"symbol": symbol, "price": price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(content, f)
        visualizer = PortfolioVisualizer(self.storage_file)
        data = visualizer.load_data()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["symbol"], symbol)

    def test_generate_ascii_chart_empty(self):
        res = generate_ascii_chart([])
        self.assertEqual(res, "NO DATA")

    def test_generate_ascii_chart_values(self):
        p1 = random.uniform(10.0, 50.0)
        p2 = random.uniform(51.0, 100.0)
        chart = generate_ascii_chart([p1, p2])
        self.assertIn(str(int(p1)), chart)
        self.assertIn(str(int(p2)), chart)
        self.assertIn("#", chart)

    def test_render_text_trend_flat(self):
        val = random.uniform(10.0, 100.0)
        self.assertEqual(render_text_trend([val]), "FLAT Trend")
        self.assertEqual(render_text_trend([val, val]), "FLAT Trend")

    def test_render_text_trend_up(self):
        base = random.uniform(10.0, 50.0)
        delta = random.uniform(1.0, 50.0)
        self.assertEqual(render_text_trend([base, base + delta]), "UP Trend (Positive Growth)")

    def test_render_text_trend_down(self):
        base = random.uniform(50.0, 100.0)
        delta = random.uniform(1.0, 40.0)
        self.assertEqual(render_text_trend([base, base - delta]), "DOWN Trend (Negative Growth)")

    def test_generate_chart_no_data(self):
        symbol = uuid.uuid4().hex
        visualizer = PortfolioVisualizer(self.storage_file)
        res = visualizer.generate_chart(symbol)
        self.assertEqual(res, "NO DATA")

    def test_generate_chart_with_matching_symbol(self):
        symbol = uuid.uuid4().hex
        price = random.uniform(100.0, 500.0)
        content = [{"symbol": symbol, "price": price}]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(content, f)
        visualizer = PortfolioVisualizer(self.storage_file)
        res = visualizer.generate_chart(symbol)
        self.assertIn(str(int(price)), res)
        self.assertIn("#", res)

    def test_market_parser_integration_safety(self):
        bad_stream = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        with patch("builtins.open", return_value=bad_stream):
            visualizer = PortfolioVisualizer(self.storage_file)
            data = visualizer.load_data()
            self.assertEqual(data, [])