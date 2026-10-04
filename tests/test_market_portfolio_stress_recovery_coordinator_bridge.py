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
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_bridge_initialization_creates_storage(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertTrue(os.path.exists(self.storage_file))
        self.assertEqual(bridge.storage_file, self.storage_file)
        self.assertEqual(bridge.monitor["status"], "initialized")

    def test_execute_recovery_workflow_success(self):
        expected_stress = {"status": "ok", "symbol": self.symbol, "shift_count": self.shifts}
        expected_recovery = {"status": "recovered", "chat": self.chat_id}

        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)

        with patch.object(bridge.pipeline, "execute", return_value=expected_stress) as mock_pipeline_exec, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline", return_value=expected_recovery) as mock_run_pipeline:

            result = bridge.execute_recovery_workflow(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            mock_pipeline_exec.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
            
            self.assertEqual(result["stress_result"], expected_stress)
            self.assertEqual(result["recovery_result"], expected_recovery)

    def test_execute_recovery_workflow_key_error_fallback(self):
        bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        err_msg = uuid.uuid4().hex

        with patch.object(bridge.pipeline, "execute", side_effect=KeyError(err_msg)) as mock_pipeline_exec, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline", return_value="success_string") as mock_run_pipeline:

            result = bridge.execute_recovery_workflow(
                self.symbol,
                self.url,
                self.telegram_token,
                self.chat_id,
                self.percentage,
                self.shifts
            )

            mock_pipeline_exec.assert_called_once()
            self.assertEqual(result["stress_result"]["status"], "simulated")
            self.assertEqual(result["stress_result"]["symbol"], self.symbol)
            self.assertEqual(result["stress_result"]["percentage"], self.percentage)
            
            self.assertEqual(result["recovery_result"], {"status": "success", "result": "success_string"})

    def test_run_stress_recovery_coordinator_success(self):
        expected_stress = {"scenario": uuid.uuid4().hex}
        expected_monitor = {"active": True, "target": self.symbol}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress) as mock_run_stress, \
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

            mock_run_stress.assert_called_once_with(self.storage_file, self.symbol, self.percentage, self.shifts)
            mock_start_new.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_monitor)

    def test_run_stress_recovery_coordinator_type_error_fallback(self):
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", side_effect=TypeError("invalid type")) as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value={"monitored": self.symbol}):

            result = run_stress_recovery_coordinator(
                storage_file=self.storage_file,
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_run_stress.assert_called_once()
            self.assertEqual(result["stress"]["status"], "simulated")
            self.assertEqual(result["stress"]["symbol"], self.symbol)
            self.assertEqual(result["stress"]["shifts"], self.shifts)

    def test_run_stress_recovery_coordinator_pipeline(self):
        expected_stress = {"pipeline_status": uuid.uuid4().hex}
        expected_recovery = {"recovery_id": uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value=expected_stress) as mock_run_stress, \
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

            mock_run_stress.assert_called_once_with(
                self.storage_file, 
                self.symbol, 
                self.percentage, 
                list(range(self.shifts))
            )
            mock_start_new.assert_called_once_with(
                self.symbol, 
                self.url, 
                self.telegram_token, 
                self.chat_id, 
                self.storage_file
            )

            self.assertEqual(result["stress"], expected_stress)
            self.assertEqual(result["recovery"], expected_recovery)

    def test_run_stress_recovery_coordinator_pipeline_with_shifts_iterable(self):
        custom_shifts = [random.randint(1, 100), random.randint(101, 200)]
        
        with patch("skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline", return_value={"status": "ok"}) as mock_run_stress, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.start_new", return_value={"status": "ok"}):

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

            mock_run_stress.assert_called_once_with(
                self.storage_file,
                self.symbol,
                self.percentage,
                custom_shifts
            )

    def test_storage_file_missing_io_handling(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

        mock_file_data = io.BytesIO(b'{"test": "data"}')
        
        with patch("os.path.exists", side_effect=[False, True]), \
             patch("builtins.open", return_value=io.StringIO("{}")) as mock_open, \
             patch("skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline") as mock_pipeline_cls:
            
            bridge = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
            mock_open.assert_called_once_with(self.storage_file, "w")
            self.assertIsNotNone(bridge)

if __name__ == '__main__':
    unittest.main()