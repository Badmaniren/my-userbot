import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.market_portfolio_stress_audit_bridge import (
    MarketPortfolioStressAuditBridge,
    run_stress_audit_bridge_pipeline
)

class TestMarketPortfolioStressAuditBridge(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.db_storage = f"db_{uuid.uuid4().hex}"
        self.audit_exporter = f"exporter_{uuid.uuid4().hex}"
        self.export_path = f"path_{uuid.uuid4().hex}"
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = {uuid.uuid4().hex: random.randint(-100, 100)}
        self.bridge = MarketPortfolioStressAuditBridge(
            storage_file=self.storage_file,
            db_storage=self.db_storage,
            audit_exporter=self.audit_exporter
        )

    def test_init_properties(self):
        rand_storage = f"sto_{uuid.uuid4().hex}"
        rand_db = f"db_{uuid.uuid4().hex}"
        rand_exp = f"exp_{uuid.uuid4().hex}"

        bridge_instance = MarketPortfolioStressAuditBridge(
            storage_file=rand_storage,
            db_storage=rand_db,
            audit_exporter=rand_exp
        )

        self.assertEqual(bridge_instance.storage_file, rand_storage)
        self.assertEqual(bridge_instance.db_storage, rand_db)
        self.assertIsNotNone(bridge_instance.pipeline)
        self.assertIsNotNone(bridge_instance.compliance_hub)

    def test_execute_stress_audit_success(self):
        mock_pipeline_result = {
            uuid.uuid4().hex: random.random(),
            "status": uuid.uuid4().hex
        }
        mock_compliance_result = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "integrity": True
        }

        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline.execute') as mock_exec, \
             patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.generate_compliance_log') as mock_gen, \
             patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.check_compliance_integrity') as mock_check:

            mock_exec.return_value = mock_pipeline_result
            mock_gen.return_value = mock_compliance_result
            mock_check.return_value = True

            result = self.bridge.execute_stress_audit(
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                export_path=self.export_path
            )

            mock_exec.assert_called_once_with(self.symbol, self.percentage, self.shifts)
            mock_gen.assert_called_once_with(self.export_path)
            mock_check.assert_called_once()

            self.assertIn("stress_results", result)
            self.assertIn("compliance_status", result)
            self.assertEqual(result["stress_results"], mock_pipeline_result)
            self.assertEqual(result["compliance_status"], mock_compliance_result)

    def test_execute_stress_audit_integrity_failure(self):
        mock_pipeline_result = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline.execute') as mock_exec, \
             patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.generate_compliance_log') as mock_gen, \
             patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.check_compliance_integrity') as mock_check:

            mock_exec.return_value = mock_pipeline_result
            mock_check.return_value = False

            with self.assertRaises(ValueError):
                self.bridge.execute_stress_audit(
                    symbol=self.symbol,
                    percentage=self.percentage,
                    shifts=self.shifts,
                    export_path=self.export_path
                )

    def test_run_stress_audit_bridge_pipeline_helper(self):
        rand_file = f"{uuid.uuid4().hex}.json"
        rand_db = f"{uuid.uuid4().hex}.sqlite"
        rand_exp = f"export_{uuid.uuid4().hex}"
        rand_sym = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_pct = round(random.uniform(1.0, 99.0), 2)
        rand_shifts = {uuid.uuid4().hex: random.uniform(-10.0, 10.0)}

        mock_audit_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_stress_audit_bridge.MarketPortfolioStressAuditBridge.execute_stress_audit') as mock_bridge_exec:
            mock_bridge_exec.return_value = mock_audit_output

            res = run_stress_audit_bridge_pipeline(
                storage_file=rand_file,
                db_storage=rand_db,
                audit_exporter=self.audit_exporter,
                symbol=rand_sym,
                percentage=rand_pct,
                shifts=rand_shifts,
                export_path=rand_exp
            )

            mock_bridge_exec.assert_called_once_with(
                symbol=rand_sym,
                percentage=rand_pct,
                shifts=rand_shifts,
                export_path=rand_exp
            )
            self.assertEqual(res, mock_audit_output)

    def test_stream_audit_processing_integration(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        mock_stream_summary = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.process_audit_stream_data') as mock_process, \
             patch('skills.market_portfolio_audit_compliance_hub.MarketPortfolioAuditComplianceHub.get_audit_stream_summary') as mock_summary:

            mock_summary.return_value = mock_stream_summary

            res = self.bridge.process_external_stream(self.export_path, stream_data)

            mock_process.assert_called_once_with(self.export_path, stream_data)
            mock_summary.assert_called_once()
            self.assertEqual(res, mock_stream_summary)

if __name__ == '__main__':
    unittest.main()