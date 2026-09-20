import unittest
import os
import uuid
import tempfile
from unittest.mock import patch
from skills.market_database_notifier import MarketDatabaseNotifier
from skills.db_storage import MarketParser


class TestMarketDatabaseNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_market_{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"fake_token_{uuid.uuid4().hex}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("skills.market_telegram_pipeline.requests.post")
    def test_notify_on_fetch_integration(self, mock_post):
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notifier = MarketDatabaseNotifier(
            storage_file=self.storage_file,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        result_message = notifier.notify_on_fetch(self.symbol, self.url)
        self.assertIn(self.symbol, result_message)

        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, (dict, list))


if __name__ == "__main__":
    unittest.main()
