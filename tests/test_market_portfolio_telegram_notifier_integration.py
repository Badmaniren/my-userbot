import unittest
import uuid
import random
from skills.market_portfolio_telegram_notifier import start_new, send_telegram_notification

class TestMarketPortfolioTelegramNotifierIntegration(unittest.TestCase):
    def test_telegram_notifier_with_random_payload(self):
        random_token = f"{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:6]}"
        random_chat_id = str(random.randint(10000000, 99999999))
        random_message = f"Integration Test Message ID: {uuid.uuid4()}"

        result_start_new = start_new(random_token, random_chat_id, random_message)
        result_alias = send_telegram_notification(random_token, random_chat_id, random_message)

        self.assertIsInstance(result_start_new, bool)
        self.assertIsInstance(result_alias, bool)
        
        self.assertEqual(result_start_new, result_alias)

if __name__ == "__main__":
    unittest.main()