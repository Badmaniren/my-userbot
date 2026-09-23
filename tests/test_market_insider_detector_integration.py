import unittest
import uuid
import random
from skills.market_insider_detector import MarketInsiderDetector

class RealMarketParser:
    def __init__(self, historical_data):
        self.historical_data = historical_data

    def get_historical_data(self, symbol):
        return self.historical_data

class RealDbStorage:
    def __init__(self):
        self.saved_alerts = []
        self.saved_events = []

    def save_alert(self, alert):
        self.saved_alerts.append(alert)

    def save_insider_event(self, run_token, event_data):
        self.saved_events.append((run_token, event_data))

class TestMarketInsiderDetectorIntegration(unittest.TestCase):
    def test_detect_insider_activity_and_analysis_integration(self):
        symbol = f"TICK_{uuid.uuid4().hex[:6]}"
        run_token = uuid.uuid4().hex

        base_volume = random.randint(1000, 5000)
        spike_volume = base_volume * 10

        historical_data = []
        for i in range(10):
            historical_data.append({
                "volume": base_volume,
                "close": 100.0 + i
            })

        spike_index = 5
        historical_data[spike_index]["volume"] = spike_volume
        historical_data[spike_index + 1]["close"] = historical_data[spike_index]["close"] * 1.05

        market_parser = RealMarketParser(historical_data)
        db_storage = RealDbStorage()

        detector = MarketInsiderDetector(db_storage=db_storage, market_parser=market_parser)

        alerts = detector.detect_insider_activity(
            symbol=symbol,
            volume_threshold_multiplier=5.0,
            price_change_threshold_pct=3.0,
            lookback_periods=10
        )

        self.assertTrue(len(alerts) > 0)
        self.assertEqual(alerts[0]["symbol"], symbol)
        self.assertEqual(alerts[0]["volume"], spike_volume)
        self.assertIn(alerts[0], db_storage.saved_alerts)

        data_payload = {
            "volume": spike_volume + random.randint(1, 100),
            "price_shift": 3.5
        }

        analysis_result = detector.analyze_activity(
            ticker=symbol,
            data_payload=data_payload,
            run_token=run_token
        )

        self.assertTrue(analysis_result["anomaly_detected"])
        self.assertEqual(analysis_result["run_token"], run_token)
        self.assertEqual(analysis_result["ticker"], symbol)

        found_event = any(event[0] == run_token for event in db_storage.saved_events)
        self.assertTrue(found_event)

if __name__ == "__main__":
    unittest.main()