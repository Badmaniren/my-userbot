import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import io

from skills.market_portfolio_monitor import start_new


class TestMarketPortfolioMonitorStartNew(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.rand_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex}"
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.rand_price = round(random.uniform(10.0, 50000.0), 2)

    @patch("skills.market_portfolio_monitor.run_pipeline")
    def test_start_new_executes_pipeline(self, mock_run_pipeline):
        start_new(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage
        )
        mock_run_pipeline.assert_called_once_with(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage
        )

    @patch("skills.market_portfolio_monitor.run_pipeline")
    def test_start_new_passes_exact_random_arguments(self, mock_run_pipeline):
        unique_symbol = f"SYM_{uuid.uuid4().hex[:4]}"
        unique_url = f"http://{uuid.uuid4().hex}.org"
        unique_token = f"TOKEN_{uuid.uuid4().hex[:6]}"
        unique_chat = f"CHAT_{random.randint(100, 999)}"
        unique_storage = f"store_{uuid.uuid4().hex[:5]}.dat"

        start_new(
            unique_symbol,
            unique_url,
            unique_token,
            unique_chat,
            unique_storage
        )

        args, kwargs = mock_run_pipeline.call_args
        called_args = args if args else tuple(kwargs.values())
        
        self.assertIn(unique_symbol, [args[0] if len(args) > 0 else kwargs.get('symbol'), kwargs.get('symbol')])
        self.assertIn(unique_url, [args[1] if len(args) > 1 else kwargs.get('url'), kwargs.get('url')])
        self.assertIn(unique_token, [args[2] if len(args) > 2 else kwargs.get('telegram_token'), kwargs.get('telegram_token')])
        self.assertIn(unique_chat, [args[3] if len(args) > 3 else kwargs.get('chat_id'), kwargs.get('chat_id')])
        self.assertIn(unique_storage, [args[4] if len(args) > 4 else kwargs.get('storage_file'), kwargs.get('storage_file')])

    @patch("skills.market_portfolio_monitor.run_pipeline")
    def test_start_new_exception_propagation(self, mock_run_pipeline):
        error_message = uuid.uuid4().hex
        mock_run_pipeline.side_effect = RuntimeError(error_message)

        with self.assertRaises(RuntimeError) as ctx:
            start_new(
                symbol=self.rand_symbol,
                url=self.rand_url,
                telegram_token=self.rand_token,
                chat_id=self.rand_chat_id,
                storage_file=self.rand_storage
            )
        self.assertIn(error_message, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()