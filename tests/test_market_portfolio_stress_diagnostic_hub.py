import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_stress_diagnostic_hub import MarketPortfolioStressDiagnosticHub
from skills import db_storage, market_portfolio_scenario_simulator

class TestMarketPortfolioStressDiagnosticHubIntegration(unittest.TestCase):
    def setUp(self):
        self.hub = MarketPortfolioStressDiagnosticHub()

    def test_stress_diagnostic_hub_real_execution(self):
        scenario_id = uuid.uuid4().hex
        random_bytes = f"CRITICAL_FAILURE_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        expected_result = {
            "scenario_id": scenario_id,
            "status": "failed",
            "signature": random.choice(["TIMEOUT", "NULL_POINTER", "SEGFAULT", "OUT_OF_MEMORY"])
        }

        with patch.object(db_storage, 'fetch_log_stream', return_value=mock_stream) as mock_fetch, \
             patch.object(market_portfolio_scenario_simulator, 'analyze_failure_signature', return_value=expected_result) as mock_analyze:

            result = self.hub.collect_and_diagnose(scenario_id)

            mock_fetch.assert_called_once_with(scenario_id)
            mock_analyze.assert_called_once_with(scenario_id, random_bytes)
            self.assertEqual(result, expected_result)
            self.assertEqual(result["scenario_id"], scenario_id)

    def test_stress_diagnostic_hub_edge_case_empty_log(self):
        scenario_id = uuid.uuid4().hex
        mock_stream = io.BytesIO(b"")

        expected_result = {
            "scenario_id": scenario_id,
            "status": "unknown",
            "signature": "EMPTY_LOG"
        }

        with patch.object(db_storage, 'fetch_log_stream', return_value=mock_stream), \
             patch.object(market_portfolio_scenario_simulator, 'analyze_failure_signature', return_value=expected_result) as mock_analyze:

            result = self.hub.collect_and_diagnose(scenario_id)

            mock_analyze.assert_called_once_with(scenario_id, b"")
            self.assertEqual(result["status"], "unknown")
            self.assertEqual(result["signature"], "EMPTY_LOG")

    def test_stress_diagnostic_hub_exception_propagation(self):
        scenario_id = uuid.uuid4().hex

        with patch.object(db_storage, 'fetch_log_stream', side_effect=RuntimeError(f"DB_FAIL_{uuid.uuid4().hex}")):
            with self.assertRaises(RuntimeError):
                self.hub.collect_and_diagnose(scenario_id)

if __name__ == '__main__':
    unittest.main()