import unittest
import io
import uuid
import random
from skills.market_macro_liquidity_monitor import (
    MacroLiquidityMonitor,
    MacroDataException,
    LiquidityMetrics,
    MarketMacroLiquidityMonitorSingleton,
    market_macro_liquidity_monitor
)

class RealDummyExtractor:
    def __init__(self, content: str, should_fail: bool = False):
        self.content = content
        self.should_fail = should_fail

    def fetch_data(self):
        if self.should_fail:
            raise RuntimeError("Extractor connection failed")
        return io.BytesIO(self.content.encode('utf-8'))

class RealDummyAnomalyDetector:
    def __init__(self, is_anomaly: bool):
        self.is_anomaly = is_anomaly

    def evaluate(self, metrics: LiquidityMetrics) -> dict:
        return {"is_anomaly": self.is_anomaly}

class RealDummyDbStorage:
    def __init__(self):
        self.saved_metrics = []

    def save(self, metrics: LiquidityMetrics):
        self.saved_metrics.append(metrics)


class TestMarketMacroLiquidityMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_metric_name = f"M_INDEX_{uuid.uuid4().hex[:6]}"
        self.random_value = round(random.uniform(100.5, 9999.9), 2)
        self.random_currency = random.choice(["USD", "EUR", "RUB", "BTC"])
        self.random_record_id = str(uuid.uuid4())

        self.valid_stream_content = f"{self.random_metric_name}:{self.random_value}:{self.random_currency}:{self.random_record_id}"

    def test_macro_liquidity_monitor_integration_success(self):
        db = RealDummyDbStorage()
        extractor = RealDummyExtractor(self.valid_stream_content)
        detector = RealDummyAnomalyDetector(is_anomaly=True)

        monitor = MacroLiquidityMonitor(
            db_storage=db,
            extractors=[extractor],
            anomaly_detector=detector
        )

        result = monitor.collect_and_analyze()

        self.assertEqual(result["recorded_id"], self.random_record_id)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["value"], self.random_value)

        self.assertEqual(len(db.saved_metrics), 1)
        saved = db.saved_metrics[0]
        self.assertEqual(saved.metric_name, self.random_metric_name)
        self.assertEqual(saved.value, self.random_value)
        self.assertEqual(saved.currency, self.random_currency)
        self.assertEqual(saved.record_id, self.random_record_id)

    def test_macro_liquidity_monitor_fallback_and_exception(self):
        failing_extractor = RealDummyExtractor("", should_fail=True)
        success_extractor = RealDummyExtractor(self.valid_stream_content)

        monitor = MacroLiquidityMonitor(
            db_storage=None,
            extractors=[failing_extractor, success_extractor],
            anomaly_detector=None
        )

        result = monitor.collect_and_analyze()
        self.assertEqual(result["recorded_id"], self.random_record_id)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["value"], self.random_value)

        bad_extractor = RealDummyExtractor("", should_fail=True)
        monitor_all_fail = MacroLiquidityMonitor(
            db_storage=None,
            extractors=[bad_extractor],
            anomaly_detector=None
        )

        with self.assertRaises(MacroDataException):
            monitor_all_fail.collect_and_analyze()

    def test_market_macro_liquidity_monitor_singleton_integration(self):
        session_id = str(uuid.uuid4())
        metric_val = round(random.uniform(1.0, 100.0), 4)
        source_name = f"source_{uuid.uuid4().hex[:4]}"

        response = market_macro_liquidity_monitor.evaluate_liquidity(
            metric=metric_val,
            metadata={
                "session_id": session_id,
                "source": source_name
            }
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["processed_id"], session_id)


if __name__ == '__main__':
    unittest.main()