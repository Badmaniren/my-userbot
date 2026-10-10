import unittest
import os
import json
import uuid
import random
import shutil
from skills.market_portfolio_realtime_stream_ingestor import start_new, market_portfolio_realtime_stream_ingestor

class MockDB:
    def __init__(self):
        self.storage = []
    def save(self, data):
        self.storage.append(data)

class MockParser:
    def parse(self, data):
        decoded = data.decode('utf-8')
        if "INVALID" in decoded:
            return {"status": "INVALID"}
        return {"status": "SUCCESS", "data": decoded, "id": str(uuid.uuid4())}

class TestMarketPortfolioIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_audit_{uuid.uuid4().hex}"
        self.context = {
            "db_storage": MockDB(),
            "market_parser": MockParser()
        }

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_full_stream_ingestion_cycle(self):
        # 1. Генерация случайных данных
        random_event_id = str(uuid.uuid4())
        random_price = random.uniform(100.0, 5000.0)
        stream_payload = f'{{"event_id": "{random_event_id}", "price": {random_price}}}'
        audit_path = os.path.join(self.test_dir, f"{random_event_id}.json")

        # 2. Этап приема (start_new)
        parsed_data = start_new(self.context, stream_source=stream_payload)
        self.assertEqual(parsed_data["status"], "SUCCESS")
        self.assertIn("id", parsed_data)

        # 3. Этап интеграции и аудита (market_portfolio_realtime_stream_ingestor)
        result = market_portfolio_realtime_stream_ingestor(parsed_data, audit_path)
        
        # 4. Проверка реальных изменений
        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(os.path.exists(audit_path), "Файл аудита не был создан")
        
        with open(audit_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["status"], "SUCCESS")
            self.assertEqual(saved_data["data"], stream_payload)

    def test_invalid_stream_rejection(self):
        # Проверка обработки некорректных данных
        invalid_payload = "INVALID_DATA"
        result = start_new(self.context, stream_source=invalid_payload)
        self.assertEqual(result["status"], "REJECTED")

if __name__ == '__main__':
    unittest.main()