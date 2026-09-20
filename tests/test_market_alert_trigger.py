import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_alert_trigger import check_market_alerts, trigger_alert_if_needed


class TestMarketAlertTrigger(unittest.TestCase):

    def test_check_market_alerts_above_threshold(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        random_url = f"https://{uuid.uuid4().hex}.com/market"
        random_storage = f"{uuid.uuid4().hex}.json"

        current_price = round(random.uniform(100.0, 1000.0), 2)
        threshold_price = current_price - round(random.uniform(1.0, 50.0), 2)

        with patch('skills.market_alert_trigger.MarketParser') as mock_parser_class, \
             patch('skills.market_alert_trigger.load_data') as mock_load_data:

            mock_parser_instance = mock_parser_class.return_value
            mock_parser_instance.fetch_price.return_value = current_price

            mock_load_data.return_value = {
                random_symbol: {"threshold": threshold_price, "condition": "above"}
            }

            result = check_market_alerts(
                symbol=random_symbol,
                url=random_url,
                storage_file=random_storage
            )

            mock_parser_class.assert_called_once_with(storage_file=random_storage)
            mock_parser_instance.fetch_price.assert_called_once_with(random_url)
            self.assertTrue(result)

    def test_check_market_alerts_below_threshold(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        random_url = f"https://{uuid.uuid4().hex}.org/api"
        random_storage = f"{uuid.uuid4().hex}.db"

        current_price = round(random.uniform(10.0, 50.0), 2)
        threshold_price = current_price + round(random.uniform(1.0, 20.0), 2)

        with patch('skills.market_alert_trigger.MarketParser') as mock_parser_class, \
             patch('skills.market_alert_trigger.load_data') as mock_load_data:

            mock_parser_instance = mock_parser_class.return_value
            mock_parser_instance.fetch_price.return_value = current_price

            mock_load_data.return_value = {
                random_symbol: {"threshold": threshold_price, "condition": "below"}
            }

            result = check_market_alerts(
                symbol=random_symbol,
                url=random_url,
                storage_file=random_storage
            )

            mock_parser_instance.fetch_price.assert_called_once_with(random_url)
            self.assertTrue(result)

    def test_check_market_alerts_no_trigger(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        random_url = f"https://{uuid.uuid4().hex}.net/feed"
        random_storage = f"{uuid.uuid4().hex}.json"

        current_price = 500.0
        threshold_price = 1000.0

        with patch('skills.market_alert_trigger.MarketParser') as mock_parser_class, \
             patch('skills.market_alert_trigger.load_data') as mock_load_data:

            mock_parser_instance = mock_parser_class.return_value
            mock_parser_instance.fetch_price.return_value = current_price

            mock_load_data.return_value = {
                random_symbol: {"threshold": threshold_price, "condition": "above"}
            }

            result = check_market_alerts(
                symbol=random_symbol,
                url=random_url,
                storage_file=random_storage
            )

            self.assertFalse(result)

    def test_trigger_alert_if_needed_stores_and_fetches(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_url = f"https://{uuid.uuid4().hex}.io/price"
        random_storage = f"{uuid.uuid4().hex}.storage"
        random_price = round(random.uniform(1000.0, 5000.0), 2)

        with patch('skills.market_alert_trigger.MarketParser') as mock_parser_class, \
             patch('skills.market_alert_trigger.fetch_and_store') as mock_fas:

            mock_parser_instance = mock_parser_class.return_value
            mock_parser_instance.fetch_price.return_value = random_price

            trigger_alert_if_needed(
                symbol=random_symbol,
                url=random_url,
                storage_file=random_storage,
                trigger_condition=True
            )

            mock_fas.assert_called_once_with(random_symbol, random_price, storage_file=random_storage)

    def test_trigger_alert_if_needed_skips_store(self):
        random_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        random_url = f"https://{uuid.uuid4().hex}.io/price"
        random_storage = f"{uuid.uuid4().hex}.storage"

        with patch('skills.market_alert_trigger.MarketParser') as mock_parser_class, \
             patch('skills.market_alert_trigger.fetch_and_store') as mock_fas:

            trigger_alert_if_needed(
                symbol=random_symbol,
                url=random_url,
                storage_file=random_storage,
                trigger_condition=False
            )

            mock_fas.assert_not_called()


if __name__ == '__main__':
    unittest.main()