import unittest
import os
import uuid
import random
import io

from skills import market_portfolio_alert_dispatcher


class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_process_stream_alert_integration(self):
        random_alert_id = uuid.uuid4().hex
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(random_alert_id)
        self.assertIsNotNone(stream_data)

    def test_process_stream_alert_with_storage_file_integration(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"BTC": 50000.0}')

        stream_data = market_portfolio_alert_dispatcher.process_stream_alert("alert_123", storage_file=self.storage_file)
        self.assertIsNotNone(stream_data)
        content = stream_data.getvalue() if hasattr(stream_data, "getvalue") else stream_data.read()
        self.assertIn(b"BTC", content)
