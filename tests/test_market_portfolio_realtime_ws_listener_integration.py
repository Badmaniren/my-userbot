import unittest
import uuid
import random
import asyncio
import os
import json
from skills.market_portfolio_realtime_ws_listener import market_portfolio_realtime_ws_listener
from skills.db_storage import db_storage
from skills.market_parser import market_parser

class TestMarketPortfolioRealtimeWsListenerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_run_id = str(uuid.uuid4())
        self.test_price = round(random.uniform(10.0, 1000.0), 4)
        self.test_symbol = f"COIN_{random.randint(100, 999)}"
        self.raw_message_payload = {
            "event_id": self.test_run_id,
            "symbol": self.test_symbol,
            "price": self.test_price,
            "timestamp": random.randint(1600000000, 1750000000)
        }
        self.output_filepath = f"test_ws_stream_{self.test_run_id}.log"

    def tearDown(self):
        if os.path.exists(self.output_filepath):
            try:
                os.remove(self.output_filepath)
            except OSError:
                pass

    def test_realtime_ws_listener_integration_flow(self):
        raw_json_string = json.dumps(self.raw_message_payload)
        
        parsed_message = market_parser.parse(raw_json_string)
        self.assertIsNotNone(parsed_message)

        listener_instance = market_portfolio_realtime_ws_listener(
            target_file=self.output_filepath,
            expected_event_id=self.test_run_id
        )

        async def run_listener_pipeline():
            await listener_instance.process_raw_message(raw_json_string)
            await db_storage.persist_stream_event(self.test_run_id, self.test_symbol, self.test_price)

        asyncio.run(run_listener_pipeline())

        self.assertTrue(os.path.exists(self.output_filepath), "Интеграционный тест не создал целевой файл лога WebSocket потока.")
        
        with open(self.output_filepath, "r") as f:
            file_content = f.read()
            self.assertIn(self.test_run_id, file_content, "Случайный UUID события не найден в выходном файле потока.")
            self.assertIn(str(self.test_price), file_content, "Случайное значение цены не найдено в потоке.")

        stored_record = db_storage.get_event_by_id(self.test_run_id)
        self.assertIsNotNone(stored_record, "Данные из WebSocket-потока не были сохранены через db_storage.")
        self.assertEqual(stored_record.get("symbol"), self.test_symbol)
        self.assertEqual(float(stored_record.get("price")), self.test_price)

if __name__ == "__main__":
    unittest.main()