import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io
import tempfile
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
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/webhook"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_creates_storage_if_missing(self):
        non_existent_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.db")
        self.assertFalse(os.path.exists(non_existent_file))

        bridge = StressRecoveryCoordinatorBridge(storage_file=non_existent_file)

        self.assertTrue(os.path.exists(non_existent_file))
        with open(non_existent_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "{}")

    def test_execute_recovery_workflow_success(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        expected_stress = {"status": "success", "symbol": self.symbol, "val": uuid.uuid4().hex}
        expected_recovery = {"status": "active", "msg": uuid.uuid4().hex}

        with patch.object(bridge.pipeline, "execute", return_value=expected_stress) as mock_pipeline_exec, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline", return_value=expected_recovery) as mock_run_pipeline:

            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_pipeline_exec.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress_result"], expected_stress)
            self.assertEqual(result["recovery_result"], {"status": "success", "result": expected_recovery})

    def test_execute_recovery_workflow_keyerror_fallback(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        expected_recovery = uuid.uuid4().hex

        with patch.object(bridge.pipeline, "execute", side_effect=KeyError(uuid.uuid4().hex)) as mock_pipeline_exec, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline", return_value=expected_recovery) as mock_run_pipeline:

            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress_result"], {"status": "simulated", "symbol": self.symbol, "percentage": self.percentage})
            self.assertEqual(result["recovery_result"], {"status": "success", "result": expected_recovery})

    def test_run_stress_recovery_coordinator_success(self):
        expected_stress = {"status": "ok", "id": uuid.uuid4().hex}
        expected_monitor = {"status": "running", "id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress) as mock_stress_pipe, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_monitor) as mock_start_new:

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_stress_pipe.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], {"status": "success", "result": expected_monitor})

    def test_run_stress_recovery_coordinator_exception_fallback(self):
        exc_message = uuid.uuid4().hex
        expected_monitor = {"status": "active"}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", side_effect=TypeError(exc_message)) as mock_stress_pipe, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_monitor) as mock_start_new:

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress"], {"status": "simulated", "symbol": self.symbol, "shifts": self.shifts})
            self.assertEqual(result["recovery"], expected_monitor)

    def test_run_stress_recovery_coordinator_pipeline_success(self):
        expected_stress = {"status": "completed", "token": uuid.uuid4().hex}
        expected_recovery = {"status": "monitored", "token": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress) as mock_stress_pipe, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_recovery) as mock_start_new:

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

            expected_shifts_iterable = list(range(self.shifts))
            mock_stress_pipe.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_iterable)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_pipeline_keyerror_fallback(self):
        err_msg = uuid.uuid4().hex
        expected_recovery = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", side_effect=KeyError(err_msg)) as mock_stress_pipe, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_recovery) as mock_start_new:

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

            expected_shifts_iterable = list(range(self.shifts))
            self.assertEqual(result["stress"], {"status": "simulated", "symbol": self.symbol, "shifts": expected_shifts_iterable})
            self.assertEqual(result["recovery"], {"status": "success", "result": expected_recovery})

if __name__ == '__main__':
    unittest.main()