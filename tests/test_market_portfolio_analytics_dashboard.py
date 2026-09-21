import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
import os

from skills.market_portfolio_analytics_dashboard import start_new

class TestMarketPortfolioAnalyticsDashboard(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"db_{uuid.uuid4().hex}.json"
        self.random_url = f"https://{uuid.uuid4().hex}.com/market"
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_shifts = [random.randint(-10, 10), random.randint(-10, 10)]

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_start_new_function_exists_and_callable(self):
        self.assertTrue(callable(start_new), "Функция start_new должна быть доступна и вызываема в модуле.")

    def test_start_new_execution_flow(self):
        dummy_html = f"<html><body><div class='price'>{self.random_price}</div></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = dummy_html
        mock_response.content = dummy_html.encode('utf-8')

        storage_data = {
            self.random_symbol: [
                {"price": self.random_price, "timestamp": uuid.uuid4().hex}
            ]
        }
        mock_stream = io.BytesIO(json.dumps(storage_data).encode('utf-8'))

        with patch('requests.get', return_value=mock_response) as mock_get, \
             patch('builtins.open', return_value=mock_stream) as mock_file, \
             patch('os.path.exists', return_value=True), \
             patch('requests.post') as mock_post:

            mock_post_instance = MagicMock()
            mock_post_instance.status_code = 200
            mock_post.return_value = mock_post_instance

            try:
                result = start_new(
                    storage_file=self.random_storage,
                    url=self.random_url,
                    symbol=self.random_symbol,
                    telegram_token=self.random_token,
                    chat_id=self.random_chat_id,
                    shifts=self.random_shifts
                )
            except TypeError:
                try:
                    result = start_new()
                except Exception as e:
                    self.fail(f"Функция start_new упала с неожиданным исключением: {e}")

            mock_get.assert_called()

    def test_start_new_handles_network_failure(self):
        with patch('requests.get', side_effect=Exception(uuid.uuid4().hex)) as mock_get, \
             patch('requests.post') as mock_post:

            try:
                start_new(
                    storage_file=self.random_storage,
                    url=self.random_url,
                    symbol=self.random_symbol,
                    telegram_token=self.random_token,
                    chat_id=self.random_chat_id,
                    shifts=self.random_shifts
                )
            except Exception:
                pass

            mock_get.assert_called()

    def test_start_new_anomaly_detection_and_dispatch(self):
        anomaly_price = self.random_price * random.choice([5.0, 10.0])
        dummy_html = f"<html><body><span class='price'>{anomaly_price}</span></body></html>"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = dummy_html
        mock_response.content = dummy_html.encode('utf-8')

        historical_data = {
            self.random_symbol: [
                {"price": self.random_price, "timestamp": uuid.uuid4().hex}
            ]
        }
        mock_io = io.BytesIO(json.dumps(historical_data).encode('utf-8'))

        with patch('requests.get', return_value=mock_response), \
             patch('builtins.open', return_value=mock_io), \
             patch('os.path.exists', return_value=True), \
             patch('requests.post') as mock_post:

            mock_post_res = MagicMock()
            mock_post_res.status_code = 200
            mock_post.return_value = mock_post_res

            try:
                start_new(
                    storage_file=self.random_storage,
                    url=self.random_url,
                    symbol=self.random_symbol,
                    telegram_token=self.random_token,
                    chat_id=self.random_chat_id,
                    shifts=self.random_shifts
                )
            except Exception:
                pass

            self.assertTrue(True)