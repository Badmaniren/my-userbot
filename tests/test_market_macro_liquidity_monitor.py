import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
from skills.market_macro_liquidity_monitor import (
    MacroLiquidityMonitor,
    MarketMacroLiquidityMonitorSingleton,
    MacroDataException,
    LiquidityMetrics,
    market_macro_liquidity_monitor
)

class TestMarketMacroLiquidityMonitor(unittest.TestCase):

    def setUp(self):
        self.metric_name_rand = f"metric_{uuid.uuid4().hex[:6]}"
        self.value_rand = round(random.uniform(10.0, 10000.0), 2)
        self.currency_rand = random.choice(["USD", "EUR", "RUB", "GBP"])
        self.record_id_rand = uuid.uuid4().hex

    def test_macro_liquidity_monitor_success(self):
        raw_data = f"{self.metric_name_rand}:{self.value_rand}:{self.currency_rand}:{self.record_id_rand}".encode('utf-8')

        mock_extractor = MagicMock()
        mock_extractor.fetch_data.return_value = io.BytesIO(raw_data)

        mock_storage = MagicMock()

        is_anomaly_rand = random.choice([True, False])
        mock_detector = MagicMock()
        mock_detector.evaluate.return_value = {"is_anomaly": is_anomaly_rand}

        monitor = MacroLiquidityMonitor(
            db_storage=mock_storage,
            extractors=[mock_extractor],
            anomaly_detector=mock_detector
        )

        result = monitor.collect_and_analyze()

        self.assertEqual(result["recorded_id"], self.record_id_rand)
        self.assertEqual(result["anomaly_detected"], is_anomaly_rand)
        self.assertEqual(result["value"], self.value_rand)
        mock_storage.save.assert_called_once()
        mock_detector.evaluate.assert_called_once()

    def test_macro_liquidity_monitor_fallback_extractor(self):
        raw_data = f"{self.metric_name_rand}:{self.value_rand}:{self.currency_rand}:{self.record_id_rand}".encode('utf-8')

        failing_extractor = MagicMock()
        failing_extractor.fetch_data.side_effect = Exception(f"error_{uuid.uuid4().hex}")

        success_extractor = MagicMock()
        success_extractor.fetch_data.return_value = io.BytesIO(raw_data)

        monitor = MacroLiquidityMonitor(
            extractors=[failing_extractor, success_extractor]
        )

        result = monitor.collect_and_analyze()

        self.assertEqual(result["recorded_id"], self.record_id_rand)
        self.assertEqual(result["value"], self.value_rand)
        failing_extractor.fetch_data.assert_called_once()
        success_extractor.fetch_data.assert_called_once()

    def test_macro_liquidity_monitor_all_extractors_fail(self):
        failing_extractor_1 = MagicMock()
        failing_extractor_1.fetch_data.side_effect = Exception(f"err_{uuid.uuid4().hex}")

        failing_extractor_2 = MagicMock()
        failing_extractor_2.fetch_data.side_effect = Exception(f"err_{uuid.uuid4().hex}")

        monitor = MacroLiquidityMonitor(
            extractors=[failing_extractor_1, failing_extractor_2]
        )

        with self.assertRaises(MacroDataException):
            monitor.collect_and_analyze()

    def test_macro_liquidity_monitor_invalid_format(self):
        bad_data = f"malformed_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_extractor = MagicMock()
        mock_extractor.fetch_data.return_value = io.BytesIO(bad_data)

        monitor = MacroLiquidityMonitor(extractors=[mock_extractor])

        with self.assertRaises(MacroDataException):
            monitor.collect_and_analyze()

    def test_singleton_evaluate_liquidity(self):
        session_id_rand = uuid.uuid4().hex
        source_rand = f"source_{uuid.uuid4().hex[:8]}"
        metric_val = round(random.uniform(0.1, 999.9), 4)

        mock_db_storage = MagicMock()

        with patch('skills.db_storage.db_storage', mock_db_storage, create=True):
            singleton = MarketMacroLiquidityMonitorSingleton()
            metadata = {
                "session_id": session_id_rand,
                "source": source_rand
            }
            res = singleton.evaluate_liquidity(metric_val, metadata)

            self.assertEqual(res["status"], "success")
            self.assertEqual(res["processed_id"], session_id_rand)
            mock_db_storage.save_record.assert_called_once_with({
                "session_id": session_id_rand,
                "liquidity_index": metric_val,
                "source": source_rand
            })

    def test_global_instance_exists(self):
        self.assertIsInstance(market_macro_liquidity_monitor, MarketMacroLiquidityMonitorSingleton)

if __name__ == '__main__':
    unittest.main()