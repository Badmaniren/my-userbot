import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
import string

from skills.market_portfolio_stress_recovery_hub import (
    StressRecoveryHub,
    run_stress_recovery_pipeline,
    execute_recovery_strategy,
    run_recovery_pipeline,
    execute_recovery
)


class TestMarketPortfolioStressRecoveryHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://{uuid.uuid4().hex[:8]}.test/api"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.threshold = round(random.uniform(0.01, 0.99), 4)

    def test_init_and_attributes(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )
        self.assertEqual(hub.storage_file, self.storage_file)
        self.assertEqual(hub.symbol, self.symbol)
        self.assertEqual(hub.url, self.url)
        self.assertEqual(hub.telegram_token, self.telegram_token)
        self.assertEqual(hub.chat_id, self.chat_id)

    def test_run_comprehensive_pipeline(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        expected_monitor_result = {"status": uuid.uuid4().hex}
        expected_stress_result = {"simulated": uuid.uuid4().hex}

        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_monitor, \
             patch("skills.market_portfolio_stress_recovery_hub.PortfolioStressScenarioPipeline") as mock_pipeline_cls:

            mock_monitor.return_value = expected_monitor_result
            mock_pipeline_instance = mock_pipeline_cls.return_value
            mock_pipeline_instance.execute.return_value = expected_stress_result

            result = hub.run_comprehensive_pipeline(self.percentage, self.shifts)

            mock_monitor.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            mock_pipeline_cls.assert_called_once_with(self.storage_file)
            mock_pipeline_instance.execute.assert_called_once_with(
                self.symbol, self.percentage, self.shifts
            )

            self.assertEqual(result["monitor"], expected_monitor_result)
            self.assertEqual(result["stress"], expected_stress_result)

    def test_generate_recovery_recommendation(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        dummy_data = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch("skills.market_portfolio_monitor.MarketParser") as mock_parser_cls:
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = dummy_data

            rec = hub.generate_recovery_recommendation(self.threshold)

            mock_parser_cls.assert_called_once_with(self.storage_file)
            mock_parser_instance.load_data.assert_called_once()

            self.assertEqual(rec["action"], "rebalance_portfolio")
            self.assertEqual(rec["symbol"], self.symbol)
            self.assertEqual(rec["threshold"], self.threshold)
            self.assertEqual(rec["data"], dummy_data)

    def test_run_stress_recovery_pipeline_helper(self):
        with patch("skills.market_portfolio_stress_recovery_hub.StressRecoveryHub.run_comprehensive_pipeline") as mock_run:
            expected_res = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_run.return_value = expected_res

            res = run_stress_recovery_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_run.assert_called_once_with(percentage=self.percentage, shifts=self.shifts)
            self.assertEqual(res, expected_res)

    def test_execute_recovery_strategy(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        random_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.market_portfolio_monitor.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = mock_stream

            res = execute_recovery_strategy(hub)

            mock_gen_cls.assert_called_once_with(self.storage_file)
            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, {"stream_dump_processed": True})

    def test_execute_recovery_strategy_none_stream(self):
        hub = StressRecoveryHub(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id
        )

        with patch("skills.market_portfolio_monitor.MarketReportGenerator") as mock_gen_cls:
            mock_gen_instance = mock_gen_cls.return_value
            mock_gen_instance.get_raw_stream_dump.return_value = None

            res = execute_recovery_strategy(hub)

            mock_gen_cls.assert_called_once_with(self.storage_file)
            mock_gen_instance.get_raw_stream_dump.assert_called_once()
            self.assertEqual(res, {"stream_dump_processed": True})

    def test_run_recovery_pipeline_helper(self):
        with patch("skills.market_portfolio_stress_recovery_hub.StressRecoveryHub.run_comprehensive_pipeline") as mock_run:
            expected_res = {uuid.uuid4().hex: random.randint(10, 50)}
            mock_run.return_value = expected_res

            res = run_recovery_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            mock_run.assert_called_once_with(percentage=self.percentage, shifts=self.shifts)
            self.assertEqual(res, expected_res)

    def test_execute_recovery_helper(self):
        with patch("skills.market_portfolio_stress_recovery_hub.run_recovery_pipeline") as mock_run_rec:
            expected_res = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_run_rec.return_value = expected_res

            res = execute_recovery(
                storage_file=self.storage_file,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id
            )

            mock_run_rec.assert_called_once_with(
                self.storage_file,
                self.symbol,
                self.percentage,
                self.shifts,
                self.url,
                self.telegram_token,
                self.chat_id
            )
            self.assertEqual(res, expected_res)