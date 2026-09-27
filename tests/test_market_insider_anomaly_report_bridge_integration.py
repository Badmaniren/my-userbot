import unittest
import uuid
import random
import os
import tempfile

from skills.market_insider_anomaly_report_bridge import market_insider_anomaly_report_bridge
from skills.market_insider_anomaly_analyzer import MarketInsiderAnomalyAnalyzer, market_insider_anomaly_analyzer
from skills.market_report_generator import MarketReportGenerator, generate_market_report


class TestMarketInsiderAnomalyReportBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.json")
        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        self.stream_data = {
            "volume": random.randint(1000, 1000000),
            "price": round(random.uniform(10.0, 500.0), 2),
            "orders_count": random.randint(50, 5000),
            "anomaly_score": round(random.uniform(0.0, 1.0), 4)
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bridge_composition_and_execution(self):
        analyzer = MarketInsiderAnomalyAnalyzer(anomaly_detector=None, alert_pipeline=None)
        reporter = MarketReportGenerator(storage_file=self.storage_file)

        self.assertIsNotNone(analyzer)
        self.assertIsNotNone(reporter)

        try:
            result = market_insider_anomaly_report_bridge(
                ticker=self.ticker,
                exchange=self.exchange,
                stream_data=self.stream_data,
                storage_file=self.storage_file
            )
        except TypeError:
            try:
                result = market_insider_anomaly_report_bridge(
                    ticker=self.ticker,
                    stream_data=self.stream_data,
                    storage_file=self.storage_file
                )
            except TypeError:
                result = market_insider_anomaly_report_bridge(self.ticker, self.stream_data)

        self.assertIsNotNone(result, "Модуль интеграции должен возвращать результат комплексного расследования.")
        
        if isinstance(result, dict):
            self.assertTrue(len(result) > 0)
        elif isinstance(result, str):
            self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()