import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_collector_agent import start_new

class TestMarketPortfolioCollectorAgentStartNew(unittest.TestCase):

    def test_start_new_executes_successfully(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{uuid.uuid4().hex}.com/market"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.db"

        with patch('skills.market_portfolio_collector_agent.run_pipeline') as mock_run_pipeline:
            mock_run_pipeline.return_value = True
            
            result = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            mock_run_pipeline.assert_called_once_with(
                rand_symbol,
                rand_url,
                rand_token,
                rand_chat,
                rand_storage
            )
            self.assertTrue(result)

    def test_start_new_handles_pipeline_exception(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_url = f"http://{uuid.uuid4().hex}.org/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(1000, 9999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        err_message = uuid.uuid4().hex

        with patch('skills.market_portfolio_collector_agent.run_pipeline', side_effect=Exception(err_message)) as mock_run_pipeline:
            with self.assertRaises(Exception) as ctx:
                start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat,
                    storage_file=rand_storage
                )
            
            self.assertIn(err_message, str(ctx.exception))
            mock_run_pipeline.assert_called_once_with(
                rand_symbol,
                rand_url,
                rand_token,
                rand_chat,
                rand_storage
            )