import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_stress_alert_emitter import emit_stress_alerts_from_report

class TestMarketPortfolioStressAlertEmitterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"stress_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(uuid.uuid4().int)[:8]
        self.url = f"https://api.test.example/v1/alert/{uuid.uuid4().hex}"
        self.shifts = [-5.0, -15.0, -25.0]
        self.severity_level = "CRITICAL"
        self.min_threshold = -20.0
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stress_alert_emitter_composition_integration(self):
        result = emit_stress_alerts_from_report(
            storage_file=self.storage_file,
            symbol=self.symbol,
            shifts=self.shifts,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Модуль должен использовать market_portfolio_stress_reporter и создать файл хранилища отчетов."
        )

        self.assertIsInstance(
            result,
            (dict, list),
            "Эмитер должен возвращать структурированный результат выполнения."
        )

if __name__ == '__main__':
    unittest.main()