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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
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
        expected_stress_output = {"status": "ok", "symbol": self.symbol, "shifts": self.shifts}
        expected_recovery_output = {"status": "success", "detail": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineClass, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MockPipelineClass.return_value
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

    def test_execute_recovery_workflow_key_error_fallback(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as MockPipelineClass, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline") as mock_run_pipeline:
            
            mock_pipeline_instance = MockPipelineClass.return_value
            mock_pipeline_instance.execute.side_effect = KeyError(uuid.uuid4().hex)
            expected_recovery_output = {"status": "success", "result": uuid.uuid4().hex}
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

            self.assertEqual(result["stress_result"], {
                "status": "simulated",
                "symbol": self.symbol,
                "percentage": self.percentage
            })
            self.assertEqual(result["recovery_result"], expected_recovery_output)

    def test_run_stress_recovery_coordinator_success(self):
        expected_stress = {"status": "executed", "val": uuid.uuid4().hex}
        expected_recovery = {"status": "running", "val": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_recovery

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
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_exceptions(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = TypeError(uuid.uuid4().hex)
            raw_non_dict_recovery = uuid.uuid4().hex
            mock_start_new.return_value = raw_non_dict_recovery

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            self.assertEqual(result["stress"], {
                "status": "simulated",
                "symbol": self.symbol,
                "shifts": self.shifts
            })
            self.assertEqual(result["recovery"], {
                "status": "success",
                "result": raw_non_dict_recovery
            })

    def test_run_stress_recovery_coordinator_pipeline(self):
        expected_stress = {"status": "pipeline_ok", "uid": uuid.uuid4().hex}
        expected_recovery = {"status": "monitor_ok", "uid": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.return_value = expected_stress
            mock_start_new.return_value = expected_recovery

            shifts_list = random.randint(2, 5)
            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=shifts_list,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            mock_run_stress.assert_called_once()
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_pipeline_key_error(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline") as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new") as mock_start_new:
            
            mock_run_stress.side_effect = KeyError(uuid.uuid4().hex)
            mock_start_new.return_value = {"status": "ok"}

            shifts_count = 3
            result = run_stress_recovery_coordinator_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                price=self.price,
                percentage=self.percentage,
                shifts=shifts_count,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                url=self.url
            )

            expected_shifts_iterable = list(range(shifts_count))
            self.assertEqual(result["stress"], {
                "status": "simulated",
                "symbol": self.symbol,
                "shifts": expected_shifts_iterable
            })

if __name__ == '__main__':
    unittest.main()