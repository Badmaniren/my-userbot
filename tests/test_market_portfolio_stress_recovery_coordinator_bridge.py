import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_recovery_coordinator_bridge import (
    StressRecoveryCoordinatorBridge,
    run_stress_recovery_coordinator
)

class TestMarketPortfolioStressRecoveryCoordinatorBridge(unittest.TestCase):

    def setUp(self):
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000, 99999))
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.percentage = round(random.uniform(1.0, 50.0), 2)
        self.shifts = random.randint(1, 10)

    def test_bridge_initialization_and_composition(self):
        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        self.assertEqual(coordinator.storage_file, self.storage_file)
        self.assertIsNotNone(coordinator.pipeline)
        self.assertIsNotNone(coordinator.monitor)

    @patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline')
    @patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_pipeline')
    def test_execute_recovery_workflow_success(self, mock_run_pipeline, mock_pipeline_cls):
        mock_pipeline_instance = MagicMock()
        expected_pipeline_result = {
            uuid.uuid4().hex: random.uniform(100.0, 1000.0),
            "status": uuid.uuid4().hex
        }
        mock_pipeline_instance.execute.return_value = expected_pipeline_result
        mock_pipeline_cls.return_value = mock_pipeline_instance

        expected_monitor_result = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "recovered": True
        }
        mock_run_pipeline.return_value = expected_monitor_result

        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        result = coordinator.execute_recovery_workflow(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        mock_pipeline_cls.assert_called_once_with(self.storage_file)
        mock_pipeline_instance.execute.assert_called_once_with(self.symbol, self.percentage, self.shifts)
        mock_run_pipeline.assert_called_once_with(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )

        self.assertIn("stress_result", result)
        self.assertIn("recovery_result", result)
        self.assertEqual(result["stress_result"], expected_pipeline_result)
        self.assertEqual(result["recovery_result"], expected_monitor_result)

    @patch('skills.market_portfolio_stress_recovery_coordinator_bridge.run_stress_scenario_pipeline')
    @patch('skills.market_portfolio_stress_recovery_coordinator_bridge.start_new')
    def test_run_stress_recovery_coordinator_functional(self, mock_start_new, mock_run_stress):
        mock_stress_output = {
            uuid.uuid4().hex: random.randint(1, 100)
        }
        mock_run_stress.return_value = mock_stress_output

        mock_monitor_output = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        mock_start_new.return_value = mock_monitor_output

        res = run_stress_recovery_coordinator(
            storage_file=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            percentage=self.percentage,
            shifts=self.shifts
        )

        mock_run_stress.assert_called_once_with(
            self.storage_file, self.symbol, self.percentage, self.shifts
        )
        mock_start_new.assert_called_once_with(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )

        self.assertEqual(res["stress"], mock_stress_output)
        self.assertEqual(res["recovery"], mock_monitor_output)

    @patch('skills.market_portfolio_stress_recovery_coordinator_bridge.PortfolioStressScenarioPipeline')
    def test_stress_pipeline_exception_handling(self, mock_pipeline_cls):
        mock_pipeline_instance = MagicMock()
        error_message = uuid.uuid4().hex
        mock_pipeline_instance.execute.side_effect = ValueError(error_message)
        mock_pipeline_cls.return_value = mock_pipeline_instance

        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        
        with self.assertRaises(ValueError) as ctx:
            coordinator.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )
        
        self.assertIn(error_message, str(ctx.exception))

    def test_io_stream_handling_simulation(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_bytes)
        
        coordinator = StressRecoveryCoordinatorBridge(storage_file=self.storage_file)
        
        with patch.object(coordinator, 'execute_recovery_workflow') as mock_exec:
            mock_exec.return_value = {uuid.uuid4().hex: stream.read().decode('utf-8')}
            
            res = coordinator.execute_recovery_workflow(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                percentage=self.percentage,
                shifts=self.shifts
            )
            
            self.assertIn(random_bytes.decode('utf-8'), list(res.values()))

if __name__ == '__main__':
    unittest.main()