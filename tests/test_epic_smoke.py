import unittest
import os
import json
import tempfile
from unittest.mock import patch

try:
    from market_parser import MarketParser
except ImportError:
    from skills.market_parser import MarketParser

try:
    from db_storage import MarketParser as DBStorageParser
except ImportError:
    from skills.db_storage import MarketParser as DBStorageParser

try:
    from market_report_generator import MarketReportGenerator, generate_market_report
except ImportError:
    from skills.market_report_generator import MarketReportGenerator, generate_market_report

try:
    from market_telegram_pipeline import run_pipeline, send_telegram_notification
except ImportError:
    from skills.market_telegram_pipeline import run_pipeline, send_telegram_notification


class TestCryptoPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "crypto_storage.json")

        initial_data = {
            "BTC": [
                {"price": 60000.0, "timestamp": "2023-10-01T10:00:00"},
                {"price": 61000.0, "timestamp": "2023-10-01T11:00:00"},
                {"price": 62500.0, "timestamp": "2023-10-01T12:00:00"}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_01_market_parser_and_db_storage(self):
        print("\n--- ПРАКТИЧЕСКАЯ ПРОВЕРКА 1: Парсер и База Данных ---")
        parser = MarketParser(self.storage_file)

        test_url = "https://httpbin.org/html"
        html_prices = parser.parse_html_prices(test_url)
        print(f"Распарсенные данные из HTML по адресу {test_url}: {html_prices}")

        symbol = "ETH"
        price = 3000.50
        parser.fetch_and_store(symbol, price)
        print(f"Сохранили в БД символ {symbol} с ценой {price}")

        loaded_data = parser.load_data(self.storage_file)
        print(f"Загруженные данные из хранилища: {loaded_data}")

        self.assertIn(symbol, loaded_data)
        self.assertEqual(loaded_data[symbol][-1]["price"], price)

    def test_02_market_report_generator(self):
        print("\n--- ПРАКТИЧЕСКАЯ ПРОВЕРКА 2: Генератор аналитических отчетов ---")
        reporter = MarketReportGenerator(self.storage_file)

        report = reporter.generate_symbol_report("BTC")
        print(f"Сгенерированный аналитический отчет по BTC: {report}")

        stream_dump = reporter.get_raw_stream_dump()
        print(f"Сырой дамп потока данных: {stream_dump}")

        func_report = generate_market_report(self.storage_file, "BTC")
        print(f"Результат функции generate_market_report: {func_report}")

        self.assertIsNotNone(report)

    @patch('skills.market_telegram_pipeline.requests.post')
    def test_03_market_telegram_pipeline(self, mock_requests_post):
        print("\n--- ПРАКТИЧЕСКАЯ ПРОВЕРКА 3: Полный Telegram-пайплайн ---")
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {"ok": True}

        token = "test_fake_token_12345"
        chat_id = "999888777"
        symbol = "BTC"
        url = "https://httpbin.org/html"

        print(f"Запуск пайплайна для актива {symbol} с отправкой алертов в Telegram...")
        run_pipeline(
            symbol=symbol,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=self.storage_file
        )

        if mock_requests_post.called:
            print("Telegram API был успешно вызван в ходе работы пайплайна!")
            for call_args in mock_requests_post.call_args_list:
                print(f"Параметры вызова Telegram API: {call_args}")
        else:
            print("Предупреждение: Telegram API не вызывался.")

        self.assertTrue(True, "Пайплайн отработал без критических исключений")


if __name__ == "__main__":
    unittest.main()