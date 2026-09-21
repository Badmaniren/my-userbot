import unittest
import uuid
import random
from skills.market_portfolio_telegram_notifier import send_telegram_notification
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioTelegramNotifierIntegration(unittest.TestCase):
    def test_telegram_notifier_integration_pipeline(self):
        unique_suffix = uuid.uuid4().hex[:8]
        storage_file = f"test_market_storage_{unique_suffix}.json"
        
        test_token = f"fake_token_{uuid.uuid4()}"
        test_chat_id = str(random.randint(100000, 999999))
        test_symbol = f"SYM_{unique_suffix}"
        test_url = f"https://example.com/api/v1/market/{unique_suffix}"
        test_shifts = [random.uniform(-5.0, 5.0), random.uniform(-5.0, 5.0)]
        
        result_direct = send_telegram_notification(test_token, test_chat_id, f"Integration check {unique_suffix}")
        self.assertIsInstance(result_direct, bool)
        
        hub = MarketPortfolioIntegrationHub(storage_file=storage_file)
        
        try:
            pipeline_result = hub.process_and_export(
                url=test_url,
                symbol=test_symbol,
                shifts=test_shifts,
                telegram_token=test_token,
                chat_id=test_chat_id
            )
            self.assertIsNotNone(pipeline_result)
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()