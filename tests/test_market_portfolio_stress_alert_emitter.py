import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.market_portfolio_stress_alert_emitter import (
    emit_stress_alerts,
    StressAlertEmitter
)

class TestMarketPortfolioStressAlertEmitter(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.severity_level = random.choice(["HIGH", "CRITICAL", "WARNING", "EMERGENCY"])
        self.min_threshold = round(random.uniform(5.0, 25.0), 2)
        self.shifts = [random.randint(-20, -1), random.randint(-50, -21)]

    def test_emit_stress_alerts_critical_drop(self):
        mock_report = {
            "symbol": self.symbol,
            "max_drawdown": self.min_threshold + round(random.uniform(1.0, 15.0), 2),
            "status": "CRITICAL"
        }

        with patch('skills.market_portfolio_stress_reporter.generate_stress_report', return_value=mock_report) as mock_report_func, \
             patch('skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts') as mock_dispatch:

            result = emit_stress_alerts(
                storage_file=self.storage_file,
                symbol=self.symbol,
                percentage=self.min_threshold + 5.0,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                min_threshold=self.min_threshold,
                severity_level=self.severity_level
            )

            mock_report_func.assert_called_once_with(self.storage_file, self.symbol, self.min_threshold + 5.0)
            mock_dispatch.assert_called_once()
            args, _ = mock_dispatch.call_args
            self.assertEqual(args[0], self.symbol)
            self.assertEqual(args[1], self.url)
            self.assertEqual(args[2], self.telegram_token)
            self.assertEqual(args[3], self.chat_id)
            self.assertTrue(result)

    def test_emit_stress_alerts_below_threshold(self):
        mock_report = {
            "symbol": self.symbol,
            "max_drawdown": self.min_threshold - round(random.uniform(0.1, 4.0), 2),
            "status": "STABLE"
        }

        with patch('skills.market_portfolio_stress_reporter.generate_stress_report', return_value=mock_report) as mock_report_func, \
             patch('skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts') as mock_dispatch:

            result = emit_stress_alerts(
                storage_file=self.storage_file,
                symbol=self.symbol,
                percentage=self.min_threshold - 2.0,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                min_threshold=self.min_threshold,
                severity_level=self.severity_level
            )

            mock_report_func.assert_called_once()
            mock_dispatch.assert_not_called()
            self.assertFalse(result)

    def test_stress_alert_emitter_class_pipeline(self):
        mock_pipeline_result = [
            {"shift": self.shifts[0], "drawdown": 12.5},
            {"shift": self.shifts[1], "drawdown": 33.2}
        ]

        emitter = StressAlertEmitter(storage_file=self.storage_file)

        with patch('skills.market_portfolio_stress_reporter.run_stress_reporting_pipeline', return_value=mock_pipeline_result) as mock_pipeline, \
             patch('skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts') as mock_dispatch:

            triggered = emitter.evaluate_and_emit(
                symbol=self.symbol,
                shifts=self.shifts,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                min_threshold=self.min_threshold,
                severity_level=self.severity_level
            )

            mock_pipeline.assert_called_once_with(self.storage_file, self.symbol, self.shifts)
            self.assertTrue(triggered)
            mock_dispatch.assert_called()

    def test_stress_alert_emitter_stream_data_handling(self):
        random_stream_content = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_content)

        emitter = StressAlertEmitter(storage_file=self.storage_file)

        with patch.object(emitter, 'get_stream_data', return_value=mock_stream) as mock_get_stream, \
             patch('skills.market_portfolio_alert_dispatcher.process_stream_alert') as mock_process_stream:

            res_stream = emitter.process_stream(uuid.uuid4().hex)

            mock_get_stream.assert_called_once()
            mock_process_stream.assert_called_once()
            self.assertEqual(res_stream.read(), random_stream_content)

if __name__ == '__main__':
    unittest.main()