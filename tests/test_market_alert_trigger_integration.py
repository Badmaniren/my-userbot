import unittest
import os
import uuid
import tempfile
from skills.market_alert_trigger import check_market_alerts
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorageParser

class TestMarketAlertTriggerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4().hex}.json")

        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = float(uuid.uuid4().int % 10000) + 50.0
        self.threshold = self.random_price - 10.0

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_alert_trigger_composition(self):
        parser_instance = MarketParser(self.storage_file)
        db_instance = DBStorageParser(self.storage_file)

        db_instance.fetch_and_store(self.symbol, self.random_price)

        loaded_data = db_instance.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)

        alert_result = check_market_alerts(
            storage_file=self.storage_file,
            symbol=self.symbol,
            threshold=self.threshold
        )

        self.assertTrue(alert_result, "Alert should be triggered when price exceeds threshold")
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must exist after real integration run")

if __name__ == '__main__':
    unittest.main()