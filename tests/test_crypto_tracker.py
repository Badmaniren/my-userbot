import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import random
import uuid
import string
import requests
from skills.crypto_tracker import CryptoTracker

class TestCryptoTracker(unittest.TestCase):

    def setUp(self):
        self.db_name = f"{uuid.uuid4().hex}.db"
        self.tracker = CryptoTracker(db_path=self.db_name)

    def tearDown(self):
        try:
            import os
            if os.path.exists(self.db_name):
                os.remove(self.db_name)
        except Exception:
            pass

    def test_fetch_prices_success(self):
        random_btc = round(random.uniform(10000.0, 90000.0), 2)
        random_eth = round(random.uniform(1000.0, 7000.0), 2)
        
        mock_response_data = {
            "bitcoin": {"usd": random_btc},
            "ethereum": {"usd": random_eth}
        }

        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            prices = self.tracker.fetch_prices()

            self.assertIsInstance(prices, dict)
            self.assertEqual(prices.get("btc"), random_btc)
            self.assertEqual(prices.get("eth"), random_eth)
            mock_get.assert_called_once()

    def test_fetch_prices_api_failure(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
            mock_get.return_value = mock_resp

            prices = self.tracker.fetch_prices()
            self.assertIsNone(prices)

    def test_fetch_prices_network_error(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            prices = self.tracker.fetch_prices()
            self.assertIsNone(prices)

    def test_calculate_percentage_difference(self):
        btc_price = float(random.randint(50000, 60000))
        eth_price = float(random.randint(3000, 4000))

        expected_diff = round(((btc_price - eth_price) / eth_price) * 100, 4)
        
        calculated_diff = self.tracker.calculate_percentage_difference(btc_price, eth_price)
        self.assertAlmostEqual(calculated_diff, expected_diff, places=2)

    def test_calculate_percentage_difference_zero_division(self):
        btc_price = float(random.randint(1000, 5000))
        eth_price = 0.0

        calculated_diff = self.tracker.calculate_percentage_difference(btc_price, eth_price)
        self.assertEqual(calculated_diff, 0.0)

    def test_save_record_to_db(self):
        random_btc = round(random.uniform(20000.0, 40000.0), 2)
        random_eth = round(random.uniform(1500.0, 2500.0), 2)
        random_diff = round(random.uniform(10.0, 90.0), 2)

        self.tracker.save_record(random_btc, random_eth, random_diff)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT btc_price, eth_price, percentage_diff FROM crypto_records")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], random_btc)
        self.assertEqual(row[1], random_eth)
        self.assertEqual(row[2], random_diff)

    def test_track_and_save_full_cycle(self):
        random_btc = round(random.uniform(40000.0, 50000.0), 2)
        random_eth = round(random.uniform(2000.0, 3000.0), 2)
        
        mock_response_data = {
            "bitcoin": {"usd": random_btc},
            "ethereum": {"usd": random_eth}
        }

        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            result = self.tracker.track_and_save()

            self.assertTrue(result)

            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT btc_price, eth_price FROM crypto_records")
            row = cursor.fetchone()
            conn.close()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], random_btc)
            self.assertEqual(row[1], random_eth)

    def test_track_and_save_failure_on_api(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_get.return_value = mock_resp

            result = self.tracker.track_and_save()
            self.assertFalse(result)

            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crypto_records")
            count = cursor.fetchone()[0]
            conn.close()

            self.assertEqual(count, 0)

if __name__ == "__main__":
    unittest.main()