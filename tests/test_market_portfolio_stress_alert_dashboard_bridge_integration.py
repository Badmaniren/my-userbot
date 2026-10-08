import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_stress_alert_dashboard_bridge import (
    StressAlertDashboardBridge
)
from skills.market_portfolio_stress_alert_emitter import StressAlertEmitter
from skills.market_report_generator import MarketReportGenerator

class TestMarketPortfolioStressAlertDashboardBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test-market-{uuid.uuid4().hex[:8]}.com/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.min_threshold = round(random.uniform(1.0, 5.0), 2)
        self.severity_level = random.choice(["HIGH", "CRITICAL", "EXTREME"])
        self.shifts = [round(random.uniform(-15.0, -5.0), 2) for _ in range(3)]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_alert_dashboard_bridge_composition(self):
        bridge = StressAlertDashboardBridge(storage_file=self.storage_file)
        
        self.assertIsInstance(bridge.emitter, StressAlertEmitter)
        self.assertIsInstance(bridge.report_generator, MarketReportGenerator)

        result_dashboard = bridge.handle_stress_event_and_generate_dashboard(
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            min_threshold=self.min_threshold,
            severity_level=self.severity_level
        )

        self.assertIsNotNone(result_dashboard)
        self.assertIn(self.symbol, str(result_dashboard))
        
        raw_dump = bridge.report_generator.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump)

if __name__ == "__main__":
    unittest.main()