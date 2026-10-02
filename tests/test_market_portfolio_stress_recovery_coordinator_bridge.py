import os
import unittest
from unittest.mock import patch, MagicMock
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
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_stress_{self.rand_suffix}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        self.url = f"https://api.random-{uuid.uuid4().hex[:6]}.com/hook"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_init_creates_storage(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        self.assertFalse(os.path.exists(self.storage_file))
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "{}")
        self.assertEqual(bridge.storage_file, self.storage_file)

    def test_execute_recovery_workflow_success(self):
        mock_stress_res = {"status": "ok", "symbol": self.symbol, "val": uuid.uuid4().hex}
        mock_recovery_res = {"status": "delivered", "id": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipelineClass, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:

            instance = MockPipelineClass.return_value
            instance.execute.return_value = mock_stress_res
            mock_run_pipeline.return_value = mock_recovery_res

            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = bridge.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertIn("stress_result", result)
            self.assertIn("recovery_result", result)
            self.assertEqual(result["stress_result"], mock_stress_res)
            self.assertEqual(result["recovery_result"], mock_recovery_res)

    def test_execute_recovery_workflow_keyerror_fallback(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as MockPipelineClass, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:

            instance = MockPipelineClass.return_value
            rand_key = uuid.uuid4().hex
            instance.execute.side_effect = KeyError(rand_key)

            non_dict_recovery = f"success_{uuid.uuid4().hex}"
            mock_run_pipeline.return_value = non_dict_recovery

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

            self.assertEqual(result["recovery_result"], {"status": "success", "result": non_dict_recovery})

    def test_run_stress_recovery_coordinator_success(self):
        mock_stress_output = {"executed": True, "uid": uuid.uuid4().hex}
        mock_monitor_output = {"notified": True, "chat": self.chat_id}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.return_value = mock_stress_output
            mock_start_new.return_value = mock_monitor_output

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

            self.assertEqual(result["stress"], mock_stress_output)
            self.assertEqual(result["recovery"], mock_monitor_output)

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.side_effect = TypeError(uuid.uuid4().hex)
            mock_start_new.return_value = {"status": "ok"}

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

    def test_run_stress_recovery_coordinator_pipeline_int_shifts(self):
        mock_stress_res = {"pipeline": uuid.uuid4().hex}
        mock_recovery_res = {"monitor": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.return_value = mock_stress_res
            mock_start_new.return_value = mock_recovery_res

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
            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, expected_shifts_iterable)
            self.assertEqual(result["stress"], mock_stress_res)
            self.assertEqual(result["recovery"], mock_recovery_res)

    def test_run_stress_recovery_coordinator_pipeline_iterable_shifts(self):
        custom_shifts = [random.randint(1, 100), random.randint(101, 200)]

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.side_effect = KeyError("test_key_error")
            mock_start_new.return_value = 12345

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
            self.assertEqual(result["stress"]["status"], "simulated")
            self.assertEqual(result["stress"]["shifts"], custom_shifts)
            self.assertEqual(result["recovery"], {"status": "success", "result": 12345})

if __name__ == '__main__':
    unittest.main()