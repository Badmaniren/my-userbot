import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):
    def setUp(self):
        self.random_suffix = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.storage_file = f"test_stress_recovery_{self.random_suffix}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.random-endpoint-{uuid.uuid4().hex[:6]}.org/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(10000000, 999999999))
        self.percentage = round(random.uniform(5.0, 45.0), 2)
        self.shifts = random.randint(1, 15)
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_init_creates_storage_if_missing(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
            
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r") as f:
            content = f.read()
            self.assertEqual(content, "{}")
        self.assertEqual(bridge.storage_file, self.storage_file)

    def test_execute_recovery_workflow_success(self):
        expected_stress_output = {"status": "ok", "symbol": self.symbol, "val": uuid.uuid4().hex}
        expected_recovery_output = {"status": "dispatched", "target": self.url}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineCls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MockPipelineCls.return_value
            mock_pipeline_instance.execute.return_value = expected_stress_output
            mock_run_pipeline.return_value = expected_recovery_output

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress_result"], expected_stress_output)
            self.assertEqual(result["recovery_result"], expected_recovery_output)

    def test_execute_recovery_workflow_fallback_on_exception(self):
        expected_recovery_output = {"status": "success_recovery"}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineCls, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MockPipelineCls.return_value
            mock_pipeline_instance.execute.side_effect = KeyError(f"Missing key {uuid.uuid4().hex}")
            mock_run_pipeline.return_value = expected_recovery_output

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress_result"]["status"], "simulated")
            self.assertEqual(result["stress_result"]["symbol"], self.symbol)
            self.assertEqual(result["stress_result"]["percentage"], self.percentage)
            self.assertEqual(result["recovery_result"], expected_recovery_output)

    def test_run_stress_recovery_coordinator_success(self):
        expected_stress = {"scenario": "passed", "id": uuid.uuid4().hex}
        expected_monitor = {"status": "started", "token_used": self.telegram_token[:5]}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_monitor

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_monitor)

    def test_run_stress_recovery_coordinator_fallback_type_error(self):
        expected_monitor = "RawStringResult"

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = TypeError(f"Type mismatch {uuid.uuid4().hex}")
            mock_start_new.return_value = expected_monitor

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress"]["status"], "simulated")
            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["stress"]["shifts"], self.shifts)
            self.assertEqual(result["recovery"], {"status": "success", "result": expected_monitor})

    def test_run_stress_recovery_coordinator_pipeline_shifts_int_conversion(self):
        expected_stress = {"pipeline_stress": uuid.uuid4().hex}
        expected_recovery = {"pipeline_recovery": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_recovery

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=self.shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            expected_shifts_arg = list(range(self.shifts))
            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_arg)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_pipeline_shifts_custom_list(self):
        custom_shifts = [random.randint(1, 100), random.randint(101, 200)]
        expected_stress = {"custom_list": True}
        expected_recovery = {"custom_list": False}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_recovery

            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, custom_shifts)
            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)