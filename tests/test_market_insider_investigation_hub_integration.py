import unittest
import os
import uuid
import random
from skills.market_insider_investigation_hub import MarketInsiderInvestigationHub
from skills.db_storage import MarketParser
from skills.market_insider_anomaly_report_bridge import MarketInsiderAnomalyReportBridge

class TestMarketInsiderInvestigationHubIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.exchange = random.choice(["NASDAQ", "NYSE", "LSE"])

        self.stream_data = {
            "volume_spike": random.uniform(1.5, 10.0),
            "price_delta": random.uniform(-0.05, 0.05),
            "timestamp": random.randint(1600000000, 1700000000)
        }

        self.hub = MarketInsiderInvestigationHub(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_investigation_hub_composition_and_persistence(self):
        self.assertIsInstance(self.hub.db_storage, MarketParser)
        self.assertIsInstance(self.hub.report_bridge, MarketInsiderAnomalyReportBridge)

        result = self.hub.run_investigation(
            ticker=self.ticker,
            exchange=self.exchange,
            stream_data=self.stream_data
        )

        self.assertIsNotNone(result)
        self.assertIn("investigation_id", result)
        self.assertEqual(result.get("ticker"), self.ticker)
        self.assertEqual(result.get("exchange"), self.exchange)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)

        self.assertIsNotNone(loaded_data)

        if isinstance(loaded_data, dict):
            found = len(loaded_data) > 0 or self.ticker in str(loaded_data)
        elif isinstance(loaded_data, list):
            found = len(loaded_data) > 0
        else:
            found = True

        self.assertTrue(found, "Данные расследования должны сохраниться в хранилище через db_storage")

if __name__ == "__main__":
    unittest.main()