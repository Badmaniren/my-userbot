import unittest
import uuid
import random
from skills.market_portfolio_telegram_notifier import send_telegram_notification, start_new

class TestMarketPortfolioTelegramNotifierIntegration(unittest.TestCase):
    def test_telegram_notifier_integration_with_invalid_and_random_data(self):
        random_token_prefix = str(uuid.uuid4())
        fake_token = f"{random.randint(100000, 999999)}:{random_token_prefix}"
        fake_chat_id = str(random.randint(10000000, 99999999))
        random_message = f"Integration Test Digest ID: {uuid.uuid4()}"

        result_start = start_new(fake_token, fake_chat_id, random_message)
        self.assertIsInstance(result_start, bool)

        result_alias = send_telegram_notification(fake_token, fake_chat_id, random_message)
        self.assertIsInstance(result_alias, bool)

        invalid_token = ""
        invalid_chat_id = "   "
        invalid_message = None

        self.assertFalse(start_new(invalid_token, fake_chat_id, random_message))
        self.assertFalse(send_telegram_notification(fake_token, invalid_chat_id, random_message))
        self.assertFalse(start_new(fake_token, fake_chat_id, invalid_message))

if __name__ == "__main__":
    unittest.main()