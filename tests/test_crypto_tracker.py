import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os
import uuid
import random
import datetime
from skills.crypto_tracker import CryptoTracker

class TestCryptoTracker(unittest.TestCase):
    def setUp(self):
        self.db_name = f"test_{uuid.uuid4().hex}.db"
        self.tracker = CryptoTracker(db_path=self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_init_db_creates_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("crypto_records", tables)
        self.assertIn("crypto_prices", tables)

    def test_calculate_percentage_difference_normal(self):
        btc = random.uniform(30000.0, 70000.0)
        eth = random.uniform(1500.0, 4000.0)
        expected = ((btc - eth) / eth) * 100.0
        result = self.tracker.calculate_percentage_difference(btc, eth)
        self.assertAlmostEqual(result, expected)

    def test_calculate_percentage_difference_zero_eth(self):
        btc = random.uniform(1000.0, 50000.0)
        eth = 0.0
        result = self.tracker.calculate_percentage_difference(btc, eth)
        self.assertEqual(result, 0.0)

    def test_fetch_prices_success(self):
        btc_val = random.uniform(40000, 60000)
        eth_val = random.uniform(2000, 4000)
        mock_response_data = {
            "bitcoin": {"usd": btc_val},
            "ethereum": {"usd": eth_val}
        }
        
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data
            mock_get.return_value = mock_resp

            prices = self.tracker.fetch_prices()
            self.assertIsNotNone(prices)
            self.assertEqual(prices["btc"], float(btc_val))
            self.assertEqual(prices["eth"], float(eth_val))

    def test_fetch_prices_failure_status(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = random.choice([400, 404, 500, 503])
            mock_get.return_value = mock_resp

            prices = self.tracker.fetch_prices()
            self.assertIsNone(prices)

    def test_fetch_prices_request_exception(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_get.side_effect = Exception(uuid.uuid4().hex)
            prices = self.tracker.fetch_prices()
            self.assertIsNone(prices)

    def test_save_record(self):
        btc = random.uniform(100, 1000)
        eth = random.uniform(10, 50)
        diff = random.uniform(-10, 10)

        record_id = self.tracker.save_record(btc, eth, diff)
        self.assertIsInstance(record_id, int)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT btc_price, eth_price, percentage_diff FROM crypto_records")
        row_rec = cursor.fetchone()
        cursor.execute("SELECT btc_price, eth_price, percentage_diff FROM crypto_prices")
        row_pr = cursor.fetchone()
        conn.close()

        self.assertEqual(row_rec[0], btc)
        self.assertEqual(row_rec[1], eth)
        self.assertEqual(row_rec[2], diff)
        self.assertEqual(row_pr[0], btc)
        self.assertEqual(row_pr[1], eth)
        self.assertEqual(row_pr[2], diff)

    def test_track_and_save_success(self):
        btc_val = random.uniform(10000, 20000)
        eth_val = random.uniform(500, 1500)
        mock_data = {
            "bitcoin": {"usd": btc_val},
            "ethereum": {"usd": eth_val}
        }

        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_data
            mock_get.return_value = mock_resp

            success = self.tracker.track_and_save()
            self.assertTrue(success)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM crypto_records")
        count_rec = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM crypto_prices")
        count_pr = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count_rec, 1)
        self.assertEqual(count_pr, 1)

    def test_track_and_save_fail(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_get.return_value = mock_resp

            success = self.tracker.track_and_save()
            self.assertFalse(success)

    def test_fetch_and_save_prices(self):
        btc_val = random.uniform(30000, 40000)
        eth_val = random.uniform(2000, 3000)
        mock_data = {
            "bitcoin": {"usd": btc_val},
            "ethereum": {"usd": eth_val}
        }

        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_data
            mock_get.return_value = mock_resp

            rec_id = self.tracker.fetch_and_save_prices()
            self.assertIsNotNone(rec_id)
            self.assertIsInstance(rec_id, int)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT btc_price FROM crypto_prices WHERE id = ?", (rec_id,))
        val = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(val, btc_val)

    def test_fetch_and_save_prices_none(self):
        with patch("skills.crypto_tracker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            rec_id = self.tracker.fetch_and_save_prices()
            self.assertIsNone(rec_id)