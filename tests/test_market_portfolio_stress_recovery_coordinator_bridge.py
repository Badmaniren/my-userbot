import os
import unittest
import uuid
import random
import tempfile
import io
from unittest.mock import patch, MagicMock
from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = f"-{random.randint(1000000, 9999999)}"
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bridge_init_creates_storage(self):
        non_existent_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.db")
        self.assertFalse(os.path.exists(non_existent_file))

        bridge = StressRecoveryCoordinatorBridge(storage_file=non_existent_file)
        self.assertTrue(os.path.exists(non_existent_file))
        self.assertEqual(bridge.storage_file, non_existent_file)
        self.assertEqual(bridge.monitor["status"], "initialized")

    def test_execute_recovery_workflow_success(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        mock_stress_res = {"status": "ok", "symbol": self.symbol, "shift_count": self.shifts}
        mock_recovery_res = {"status": "delivered", "target": self.chat_id}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline_class, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline', return_value=mock_recovery_res) as mock_run_pipeline:
            
            mock_pipeline_instance = mock_pipeline_class.return_value
            mock_pipeline_instance.execute.return_value = mock_stress_res

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

            self.assertEqual(result["stress_result"], mock_stress_res)
            self.assertEqual(result["recovery_result"], mock_recovery_res)

    def test_execute_recovery_workflow_pipeline_exception_fallback(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        mock_recovery_res = "RawStringResult"

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline_class, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline', return_value=mock_recovery_res) as mock_run_pipeline:
            
            mock_pipeline_instance = mock_pipeline_class.return_value
            mock_pipeline_instance.execute.side_effect = KeyError(uuid.uuid4().hex)

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
            self.assertEqual(result["recovery_result"], {"status": "success", "result": "RawStringResult"})

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_output = {"executed": True, "val": uuid.uuid4().hex}
        mock_monitor_output = {"notified": True, "id": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_output) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_monitor_output) as mock_start_new:

            res = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_stress_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(res["stress"], mock_stress_output)
            self.assertEqual(res["recovery"], mock_monitor_output)

    def test_run_stress_recovery_coordinator_type_error_fallback(self):
        mock_monitor_output = {"status": "dispatched"}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', side_effect=TypeError("Bad type")) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_monitor_output) as mock_start_new:

            res = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(res["stress"]["status"], "simulated")
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["stress"]["shifts"], self.shifts)
            self.assertEqual(res["recovery"], mock_monitor_output)

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        mock_stress_res = {"pipeline_status": "ok"}
        mock_recovery_res = "NonDictResult"

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_res) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_recovery_res) as mock_start_new:

            res = run_stress_recovery_coordinator_pipeline(
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
            mock_stress_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_arg)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(res["stress"], mock_stress_res)
            self.assertEqual(res["recovery"], {"status": "success", "result": "NonDictResult"})

    def test_run_stress_recovery_coordinator_pipeline_custom_shifts_list(self):
        custom_shifts = [random.randint(1, 100), random.randint(101, 200)]
        mock_stress_res = {"custom": True}
        mock_recovery_res = {"ok": True}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', return_value=mock_stress_res) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value=mock_recovery_res) as mock_start_new:

            res = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_stress_func.assert_called_once_with(self.storage_file, self.symbol, self.percentage, custom_shifts)
            self.assertEqual(res["stress"], mock_stress_res)

    def test_run_stress_recovery_coordinator_pipeline_exception(self):
        custom_shifts = [random.randint(1, 50)]

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline', side_effect=KeyError("Missing key")) as mock_stress_func, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new', return_value={"ok": True}) as mock_start_new:

            res = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            self.assertEqual(res["stress"]["status"], "simulated")
            self.assertEqual(res["stress"]["symbol"], self.symbol)
            self.assertEqual(res["stress"]["shifts"], custom_shifts)