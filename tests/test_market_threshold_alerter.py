import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_threshold_alerter import check_threshold_and_alert


class TestMarketThresholdAlerter(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{random.randint(100, 999)}"
        self.threshold = round(random.uniform(10.0, 1000.0), 2)
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"{uuid.uuid4().hex}.db"

    @patch('skills.market_threshold_alerter.MarketParser')
    def test_check_threshold_no_url_returns_parser(self, mock_parser_cls):
        mock_instance = mock_parser_cls.return_value

        result = check_threshold_and_alert(
            symbol=self.symbol,
            url=None,
            threshold=self.threshold,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        mock_parser_cls.assert_called_once_with(storage_file=self.storage_file)
        self.assertEqual(result, mock_instance)

    @patch('skills.market_threshold_alerter.send_telegram_notification')
    @patch('skills.market_threshold_alerter.MarketParser')
    def test_check_threshold_exceeded_triggers_alert_and_store(self, mock_parser_cls, mock_send_telegram):
        mock_instance = mock_parser_cls.return_value
        high_price = self.threshold + round(random.uniform(1.0, 50.0), 2)
        mock_instance.fetch_price.return_value = high_price

        result = check_threshold_and_alert(
            symbol=self.symbol,
            url=self.url,
            threshold=self.threshold,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        mock_parser_cls.assert_called_once_with(storage_file=self.storage_file)
        mock_instance.fetch_price.assert_called_once_with(self.url)

        expected_message = f"Threshold exceeded for {self.symbol}: {high_price}"
        mock_send_telegram.assert_called_once_with(self.token, self.chat_id, expected_message)
        mock_instance.fetch_and_store.assert_called_once_with(self.symbol, high_price)
        self.assertEqual(result, high_price)

    @patch('skills.market_threshold_alerter.send_telegram_notification')
    @patch('skills.market_threshold_alerter.MarketParser')
    def test_check_threshold_not_exceeded_no_alert(self, mock_parser_cls, mock_send_telegram):
        mock_instance = mock_parser_cls.return_value
        low_price = self.threshold - round(random.uniform(1.0, 50.0), 2)
        mock_instance.fetch_price.return_value = low_price

        result = check_threshold_and_alert(
            symbol=self.symbol,
            url=self.url,
            threshold=self.threshold,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        mock_parser_cls.assert_called_once_with(storage_file=self.storage_file)
        mock_instance.fetch_price.assert_called_once_with(self.url)

        mock_send_telegram.assert_not_called()
        mock_instance.fetch_and_store.assert_not_called()
        self.assertEqual(result, low_price)

    @patch('skills.market_threshold_alerter.send_telegram_notification')
    @patch('skills.market_threshold_alerter.MarketParser')
    def test_check_threshold_none_price_no_action(self, mock_parser_cls, mock_send_telegram):
        mock_instance = mock_parser_cls.return_value
        mock_instance.fetch_price.return_value = None

        result = check_threshold_and_alert(
            symbol=self.symbol,
            url=self.url,
            threshold=self.threshold,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        mock_instance.fetch_price.assert_called_once_with(self.url)
        mock_send_telegram.assert_not_called()
        mock_instance.fetch_and_store.assert_not_called()
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()