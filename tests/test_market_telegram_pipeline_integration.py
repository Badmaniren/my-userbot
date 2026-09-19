import unittest
import os
import uuid
import random
from unittest.mock import patch
from skills.market_telegram_pipeline import run_market_telegram_pipeline

class TestMarketTelegramPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.chat_id = str(random.randint(1000000, 9999999))
        self.token = f"{random.randint(100000, 999999)}:ABC-DEF{uuid.uuid4().hex[:8]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    @patch("skills.market_telegram_pipeline.requests.post")
    def setUp_and_run(self, mock_post):
        mock_post.return_value.status_code = 200
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.token
        )
        return result, mock_post

    def test_pipeline_integration_flow(self):
        mock_post_response = type('obj', (object,), {'status_code': 200})()
        
        with patch("skills.market_telegram_pipeline.requests.post", return_value=mock_post_response) as mock_post:
            result = run_market_telegram_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                chat_id=self.chat_id,
                url=self.url,
                telegram_token=self.token
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["sent_symbol"], self.symbol)
            self.assertIn("sent_price", result)

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
            self.assertIn(self.token, args[0])
            self.assertEqual(kwargs["json"]["chat_id"], self.chat_id)
            self.assertIn(self.symbol, kwargs["json"]["text"])

if __name__ == "__main__":
    unittest.main()