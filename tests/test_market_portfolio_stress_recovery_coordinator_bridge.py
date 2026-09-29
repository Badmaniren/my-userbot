import os
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator,
    run_stress_recovery_coordinator_pipeline
)

class TestStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_stress_recovery_{self.random_suffix}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        self.url = f"https://api.{uuid.uuid4().hex[:6]}.com/hook"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = f"-{random.randint(100000,999999)}"
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_init_and_storage_creation(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline_cls:
            mock_pipeline_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance

            coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            self.assertEqual(coordinator.storage_file, self.storage_file)
            mock_pipeline_cls.assert_called_once_with(self.storage_file)

    def test_execute_recovery_workflow_success(self):
        expected_stress = {"status": f"stress_ok_{uuid.uuid4().hex[:4]}", "val": random.randint(1, 100)}
        expected_recovery = {"status": f"recovery_ok_{uuid.uuid4().hex[:4]}", "val": random.randint(101, 200)}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline_cls, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:

            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.execute.return_value = expected_stress
            mock_pipeline_cls.return_value = mock_pipeline_instance

            mock_run_pipeline.return_value = expected_recovery

            coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = coordinator.execute_recovery_workflow(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            self.assertTrue(os.path.exists(self.storage_file))
            mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            self.assertEqual(result["stress_result"], expected_stress)
            self.assertEqual(result["recovery_result"], expected_recovery)

    def test_execute_recovery_workflow_keyerror_fallback(self):
        expected_recovery = {"status": f"recovered_{uuid.uuid4().hex[:4]}"}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline') as mock_pipeline_cls, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline') as mock_run_pipeline:

            mock_pipeline_instance = MagicMock()
            mock_pipeline_instance.execute.side_effect = KeyError(f"Missing_{uuid.uuid4().hex[:4]}")
            mock_pipeline_cls.return_value = mock_pipeline_instance

            mock_run_pipeline.return_value = expected_recovery

            coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            result = coordinator.execute_recovery_workflow(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            expected_fallback = {
                "status": "simulated",
                "symbol": self.symbol,
                "percentage": self.percentage
            }
            self.assertEqual(result["stress_result"], expected_fallback)
            self.assertEqual(result["recovery_result"], expected_recovery)

    def test_run_stress_recovery_coordinator_success(self):
        expected_stress = {"metric": f"val_{uuid.uuid4().hex[:4]}"}
        expected_monitor = {"metric": f"mon_{uuid.uuid4().hex[:4]}"}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_monitor

            result = run_stress_recovery_coordinator(
                self.storage_file,
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            self.assertTrue(os.path.exists(self.storage_file))
            mock_run_stress.assert_called_once_with(
                self.storage_file, self.symbol, self.percentage, self.shifts
            )
            mock_start_new.assert_called_once_with(
                self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
            )
            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_monitor)

    def test_run_stress_recovery_coordinator_exceptions(self):
        for err_class in (KeyError, TypeError):
            with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
                 patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

                mock_run_stress.side_effect = err_class("Triggered test exception")
                expected_monitor = {"status": f"started_{uuid.uuid4().hex[:4]}"}
                mock_start_new.return_value = expected_monitor

                result = run_stress_recovery_coordinator(
                    self.storage_file,
                    self.symbol,
                    self.url,
                    self.telegram_token,
                    self.chat_id,
                    self.percentage,
                    self.shifts
                )

                expected_fallback = {
                    "status": "simulated",
                    "symbol": self.symbol,
                    "shifts": self.shifts
                }
                self.assertEqual(result["stress"], expected_fallback)
                self.assertEqual(result["recovery"], expected_monitor)

    def test_run_stress_recovery_coordinator_pipeline_with_int_shifts(self):
        expected_stress = {"run_id": uuid.uuid4().hex}
        expected_recovery = {"run_id": uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

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

            expected_shifts_list = list(range(self.shifts))
            mock_run_stress.assert_called_once_with(
                self.storage_file, self.symbol, self.percentage, expected_shifts_list
            )
            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_pipeline_with_list_shifts(self):
        custom_shifts = [random.randint(1, 100), random.randint(101, 200)]
        expected_stress = {"custom": True}
        expected_recovery = {"custom": False}

        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

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

            mock_run_stress.assert_called_once_with(
                self.storage_file, self.symbol, self.percentage, custom_shifts
            )
            self.assertEqual(result["stress"], expected_stress)

    def test_run_stress_recovery_coordinator_pipeline_exception_handling(self):
        with patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline') as mock_run_stress, \
             patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new') as mock_start_new:

            mock_run_stress.side_effect = TypeError("Type mismatch error")
            mock_start_new.return_value = {"monitor_id": uuid.uuid4().hex}

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

            expected_shifts_list = list(range(self.shifts))
            expected_fallback = {
                "status": "simulated",
                "symbol": self.symbol,
                "shifts": expected_shifts_list
            }
            self.assertEqual(result["stress"], expected_fallback)


if __name__ == '__main__':
    unittest.main()