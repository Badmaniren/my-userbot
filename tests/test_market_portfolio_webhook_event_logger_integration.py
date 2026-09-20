import unittest
import os
import uuid
import random
import tempfile
from skills.market_portfolio_webhook_event_logger import (
    WebhookEventLogger
)
from skills.market_portfolio_webhook_sync import (
    MarketPortfolioWebhookSync
)
from skills.market_portfolio_data_exporter import (
    PortfolioDataExporter
)

class TestMarketPortfolioWebhookEventLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.webhook_url = f"https://api.test-gateway.local/webhook/{uuid.uuid4()}"
        
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        
        self.webhook_sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        self.data_exporter = PortfolioDataExporter(self.storage_file)
        
        self.event_logger = WebhookEventLogger(
            storage_file=self.storage_file, 
            webhook_url=self.webhook_url
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_webhook_event_logger_composition_and_execution(self):
        self.webhook_sync.store_initial_state(self.symbol, self.price)
        
        sync_result = self.webhook_sync.trigger_webhook_sync(self.symbol, self.price)
        
        logged_event_id = str(uuid.uuid4())
        logged_status = self.event_logger.log_and_process_event(
            event_id=logged_event_id, 
            symbol=self.symbol, 
            price=self.price,
            sync_metadata=sync_result
        )

        self.assertTrue(logged_status, "Логгер должен успешно подтвердить обработку вебхука.")

        export_data = self.data_exporter.export_data("http://localhost/dummy", [1, 2, 3])
        
        self.assertIsInstance(export_data, dict, "Экспортер данных должен вернуть словарь после логирования.")
        
        loaded_events = self.event_logger.load_logged_events()
        self.assertIn(logged_event_id, str(loaded_events), "Случайный ID события должен присутствовать в хранилище логов.")
        
        stream_data = self.data_exporter.export_stream()
        self.assertIsNotNone(stream_data, "Экспорт потока данных должен вернуть непустой объект.")

if __name__ == '__main__':
    unittest.main()