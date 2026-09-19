import unittest
import sqlite3
import os
import uuid
from skills.crypto_tracker import CryptoTracker

class TestCryptoTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_name = f"test_crypto_{uuid.uuid4().hex}.db"
        self.tracker = CryptoTracker(db_path=self.db_name)

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_database_initialization_and_saving_pipeline(self):
        self.assertTrue(os.path.exists(self.db_name))

        random_btc = float(uuid.uuid4().int % 100000 + 1)
        random_eth = float(uuid.uuid4().int % 10000 + 1)
        
        diff = self.tracker.calculate_percentage_difference(random_btc, random_eth)
        expected_diff = ((random_btc - random_eth) / random_eth) * 100.0
        self.assertAlmostEqual(diff, expected_diff)

        record_id = self.tracker.save_record(random_btc, random_eth, diff)
        self.assertIsNotNone(record_id)
        self.assertGreater(record_id, 0)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT btc_price, eth_price, percentage_diff FROM crypto_records WHERE id = ?", (record_id,))
        row_records = cursor.fetchone()
        
        cursor.execute("SELECT btc_price, eth_price, percentage_diff FROM crypto_prices WHERE id = ?", (record_id,))
        row_prices = cursor.fetchone()
        
        conn.close()

        self.assertIsNotNone(row_records)
        self.assertIsNotNone(row_prices)

        self.assertEqual(row_records[0], random_btc)
        self.assertEqual(row_records[1], random_eth)
        self.assertEqual(row_records[2], expected_diff)

        self.assertEqual(row_prices[0], random_btc)
        self.assertEqual(row_prices[1], random_eth)
        self.assertEqual(row_prices[2], expected_diff)

if __name__ == "__main__":
    unittest.main()