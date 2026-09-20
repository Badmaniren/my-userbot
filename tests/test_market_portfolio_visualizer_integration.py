import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_visualizer import PortfolioVisualizer, generate_ascii_chart, render_text_trend
from skills.db_storage import MarketParser

class TestPortfolioVisualizerIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_suffix = str(uuid.uuid4())[:8]
        self.storage_file = f"test_portfolio_{self.unique_suffix}.json"

        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_portfolio_visualizer_real_integration(self):
        symbol = f"TICK_{random.randint(1000, 9999)}"
        parser = MarketParser(self.storage_file)

        price_1 = round(random.uniform(100.0, 150.0), 2)
        price_2 = round(random.uniform(151.0, 200.0), 2)
        price_3 = round(random.uniform(201.0, 250.0), 2)

        parser.fetch_and_store(symbol, price_1)
        parser.fetch_and_store(symbol, price_2)
        parser.fetch_and_store(symbol, price_3)

        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан реальным модулем db_storage")

        visualizer = PortfolioVisualizer(self.storage_file)
        loaded_data = visualizer.load_data()

        self.assertIsInstance(loaded_data, list, "Данные должны загружаться в виде списка")
        self.assertGreaterEqual(len(loaded_data), 3, "Хранилище должно содержать как минимум 3 записи")

        chart_output = visualizer.generate_chart(symbol)
        self.assertNotEqual(chart_output, "NO DATA", "Генератор графиков не должен возвращать NO DATA для существующих цен")
        self.assertIn("|", chart_output, "ASCII график должен содержать разделители строк")

        prices = [item.get("price") for item in loaded_data if "price" in item]
        trend_output = render_text_trend(prices)
        self.assertIn("UP Trend", trend_output, "Рост цен должен определяться как восходящий тренд")

    def test_portfolio_visualizer_empty_data(self):
        visualizer = PortfolioVisualizer(self.storage_file)
        non_existent_symbol = f"NONE_{uuid.uuid4()}"

        chart_output = visualizer.generate_chart(non_existent_symbol)
        self.assertEqual(chart_output, "NO DATA", "Для несуществующего символа должен возвращаться NO DATA")

        empty_trend = render_text_trend([])
        self.assertEqual(empty_trend, "FLAT Trend", "Для пустого набора данных тренд должен быть FLAT")

if __name__ == "__main__":
    unittest.main()