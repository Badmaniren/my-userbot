import unittest
import sqlite3
import os
import uuid
import random
import time
from skills.crypto_tracker import CryptoTracker

class TestCryptoTrackerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.db_name = f"test_crypto_{uuid.uuid4().hex}.db"
        self.tracker = CryptoTracker(db_path=self.db_name)
        
    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
            
    def test_real_api_and_database_integration(self):
        random_salt = random.randint(1000, 9999)
        
        record_id = self.tracker.fetch_and_save_prices()
        
        self.assertIsNotNone(record_id, "Метод должен возвращать идентификатор сохраненной записи")
        
        self.assertTrue(os.path.exists(self.db_name), "Файл базы данных SQLite должен быть создан")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertGreater(len(tables), 0, "В базе данных должны быть созданы таблицы")
        
        cursor.execute("SELECT * FROM crypto_prices WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        self.assertIsNotNone(row, f"Запись с сгенерированным ID {record_id} должна существовать в базе данных")
        
        db_id, btc_price, eth_price, diff_percent, timestamp = row[-5:] if len(row) >= 5 else row
        
        self.assertIsInstance(btc_price, (int, float))
        self.assertIsInstance(eth_price, (int, float))
        self.assertIsInstance(diff_percent, (int, float))
        self.assertGreater(btc_price, 0, "Цена BTC должна быть больше нуля")
        self.assertGreater(eth_price, 0, "Цена ETH должна быть больше нуля")
        self.assertIsNotNone(timestamp, "Метка времени должна быть сохранена")

if __name__ == '__main__':
    unittest.main()