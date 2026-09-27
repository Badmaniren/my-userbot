import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{uuid.uuid4().hex}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_init(self):
        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertEqual(coordinator.storage_file, self.storage_file)
        self.assertIsNotNone(coordinator.monitor)
        self.assertEqual(coordinator.monitor["storage"], self.storage_file)

    def test_execute_recovery_workflow(self):
        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        
        expected_stress = {"status": f"stress_ok_{uuid.uuid4().hex}"}
        expected_recovery = {"status": f"recovery_ok_{uuid.uuid4().hex}"}

        with patch.object(coordinator.pipeline, "execute", return_value=expected_stress) as mock_exec, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline", return_value=expected_recovery) as mock_run:
            
            result = coordinator.execute_recovery_workflow(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            mock_exec.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
            
            self.assertEqual(result["stress_result"], expected_stress)
            self.assertEqual(result["recovery_result"], expected_recovery)

    def test_run_stress_recovery_coordinator(self):
        expected_stress_output = {"data": f"stress_run_{uuid.uuid4().hex}"}
        expected_monitor_output = {"data": f"monitor_run_{uuid.uuid4().hex}"}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress_output) as mock_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_monitor_output) as mock_start:

            result = run_stress_recovery_coordinator(
                self.storage_file,
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            mock_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress_output)
            self.assertEqual(result["recovery"], expected_monitor_output)

    def test_run_stress_recovery_coordinator_pipeline_file_creation(self):
        expected_stress_output = {"result": f"stress_pipe_{uuid.uuid4().hex}"}
        expected_recovery_output = {"result": f"recovery_pipe_{uuid.uuid4().hex}"}

        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress_output) as mock_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_recovery_output) as mock_start:

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

            self.assertTrue(os.path.exists(self.storage_file))
            with open(self.storage_file, "r") as f:
                content = f.read()
            self.assertEqual(content, "{}")

            mock_stress.assert_called_once()
            args, _ = mock_stress.call_args
            self.assertEqual(args[0], self.storage_file)
            self.assertEqual(args[1], self.symbol)
            self.assertEqual(args[2], self.percentage)
            self.assertEqual(args[3], list(range(self.shifts)))

            mock_start.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress_output)
            self.assertEqual(result["recovery"], expected_recovery_output)

    def test_run_stress_recovery_coordinator_pipeline_iterable_shifts(self):
        expected_stress_output = {"result": f"stress_iter_{uuid.uuid4().hex}"}
        expected_recovery_output = {"result": f"recovery_iter_{uuid.uuid4().hex}"}

        custom_shifts = [random.randint(10, 20), random.randint(30, 40)]

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress_output) as mock_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value=expected_recovery_output) as mock_start:

            run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=custom_shifts,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_stress.assert_called_once()
            args, _ = mock_stress.call_args
            self.assertEqual(args[3], custom_shifts)