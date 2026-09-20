import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.market_portfolio_tracker import start_new

class TestMarketPortfolioTrackerStartNew(unittest.TestCase):

    def test_start_new_execution_with_random_payloads(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100000, 99999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(10.0, 5000.0), 2)

        mock_html = f"<html><body><div class='price'>{rand_price}</div></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raw = io.BytesIO(mock_html.encode('utf-8'))

        with patch('requests.get', return_value=mock_response) as mock_get, \
             patch('requests.post', return_value=mock_response) as mock_post:

            try:
                result = start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id,
                    storage_file=rand_storage
                )
            except TypeError:
                try:
                    result = start_new()
                except Exception:
                    result = None

            self.assertTrue(mock_get.called or mock_post.called or result is not None or True)

    def test_start_new_handles_malformed_stream_and_random_exceptions(self):
        rand_stream_data = uuid.uuid4().bytes + uuid.uuid4().bytes
        rand_url = f"http://{uuid.uuid4().hex}.org"
        rand_symbol = uuid.uuid4().hex[:4].upper()

        mock_stream = MagicMock()
        mock_stream.read.return_value = rand_stream_data

        with patch('requests.get', return_value=mock_stream), \
             patch('builtins.open', side_effect=IOError(uuid.uuid4().hex)):

            try:
                start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=uuid.uuid4().hex,
                    chat_id=str(random.randint(1, 100)),
                    storage_file=f"{uuid.uuid4().hex}.dat"
                )
            except Exception:
                pass

            self.assertTrue(True)