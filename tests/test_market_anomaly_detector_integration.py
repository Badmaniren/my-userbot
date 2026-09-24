import unittest
import uuid
import random
import time
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.db_storage import DBStorage
from skills.market_parser import MarketParser
from skills.market_portfolio_alert_event_sink import MarketPortfolioAlertEventSink


class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.db_storage = DBStorage()
        self.market_parser = MarketParser()
        self.alert_sink = MarketPortfolioAlertEventSink()
        self.detector = MarketAnomalyDetector(
            db_storage=self.db_storage,
            market_parser=self.market_parser,
            market_portfolio_alert_event_sink=self.alert_sink
        )

    def test_detect_insider_activity_spike(self):
        test_ticker = f"STK-{uuid.uuid4().hex[:6].upper()}"
        correlation_id = str(uuid.uuid4())

        base_price = random.uniform(100.0, 200.0)
        base_volume = random.randint(5000, 10000)

        for i in range(10):
            self.db_storage.save_market_state(
                ticker=test_ticker,
                price=base_price + random.uniform(-0.5, 0.5),
                volume=base_volume + random.randint(-100, 100),
                timestamp=time.time() - (3600 * (11 - i))
            )

        anomaly_price = base_price * (1.0 + random.uniform(0.15, 0.30))
        anomaly_volume = base_volume * random.randint(10, 20)

        result = self.detector.analyze_and_report(
            ticker=test_ticker,
            current_price=anomaly_price,
            current_volume=anomaly_volume,
            trace_id=correlation_id
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['ticker'], test_ticker)
        self.assertEqual(result['analysis_id'], correlation_id)
        self.assertTrue(result['is_anomaly'], "Detector failed to identify significant spike")
        self.assertIn('confidence_score', result)

        persisted_anomaly = self.db_storage.get_anomaly_record(correlation_id)
        self.assertIsNotNone(persisted_anomaly)
        self.assertEqual(persisted_anomaly['detected_ticker'], test_ticker)
        self.assertGreater(persisted_anomaly['volume_ratio'], 5.0)

        last_event = self.alert_sink.get_last_event_by_type("MARKET_ANOMALY")
        self.assertIsNotNone(last_event)
        self.assertEqual(last_event['payload']['ticker'], test_ticker)
        self.assertEqual(last_event['payload']['correlation_id'], correlation_id)

    def test_ignore_normal_market_fluctuations(self):
        test_ticker = f"NORM-{uuid.uuid4().hex[:6].upper()}"
        safe_id = str(uuid.uuid4())

        normal_price = random.uniform(50.0, 60.0)
        normal_volume = random.randint(1000, 1100)

        result = self.detector.analyze_and_report(
            ticker=test_ticker,
            current_price=normal_price + 0.05,
            current_volume=normal_volume + 10,
            trace_id=safe_id
        )

        self.assertFalse(result['is_anomaly'])

        db_check = self.db_storage.get_anomaly_record(safe_id)
        self.assertIsNone(db_check)


if __name__ == "__main__":
    unittest.main()
