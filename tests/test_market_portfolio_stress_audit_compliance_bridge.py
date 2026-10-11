import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_stress_audit_compliance_bridge import MarketPortfolioStressAuditComplianceBridge

class TestMarketPortfolioStressAuditComplianceBridge(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.compliance_hub = MagicMock()
        self.report_generator = MagicMock()
        self.exporter_v2 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.alert_dispatcher = MagicMock()
        self.scenario_executor = MagicMock()
        self.allocator = MagicMock()

        self.bridge = MarketPortfolioStressAuditComplianceBridge(
            db_storage=self.db_storage,
            market_portfolio_audit_compliance_hub=self.compliance_hub,
            market_report_generator=self.report_generator,
            market_portfolio_stress_audit_exporter_v2=self.exporter_v2,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_stress_scenario_executor_bridge=self.scenario_executor,
            market_portfolio_ml_stress_adaptive_allocator=self.allocator
        )

    def test_audit_and_sync_with_hub(self):
        instance_id = uuid.uuid4().hex
        audit_tag = uuid.uuid4().hex
        expected_result = {"tag": audit_tag, "level": random.randint(1, 99)}
        self.compliance_hub.verify_audit_trail.return_value = expected_result

        result = self.bridge.audit_and_sync(instance_id, audit_tag)

        self.db_storage.save_transaction.assert_called_once_with(instance_id, audit_tag)
        self.compliance_hub.verify_audit_trail.assert_called_once_with(instance_id, audit_tag)
        self.assertEqual(result, expected_result)

    def test_audit_and_sync_without_hub(self):
        instance_id = uuid.uuid4().hex
        audit_tag = uuid.uuid4().hex
        bridge_no_hub = MarketPortfolioStressAuditComplianceBridge(
            db_storage=self.db_storage,
            market_portfolio_audit_compliance_hub=None
        )

        result = bridge_no_hub.audit_and_sync(instance_id, audit_tag)

        self.db_storage.save_transaction.assert_called_once_with(instance_id, audit_tag)
        self.assertEqual(result, {"tag": audit_tag, "level": 100})

    def test_export_regulatory_package_success(self):
        report_id = uuid.uuid4().hex
        stream_content = uuid.uuid4().bytes
        expected_export_result = {"exported": True, "id": report_id}

        mock_stream = io.BytesIO(stream_content)
        self.report_generator.generate_report_stream.return_value = mock_stream
        self.exporter_v2.process_export.return_value = expected_export_result

        result = self.bridge.export_regulatory_package(report_id)

        self.report_generator.generate_report_stream.assert_called_once_with(report_id)
        self.exporter_v2.process_export.assert_called_once_with(stream_content)
        self.assertEqual(result, expected_export_result)

    def test_export_regulatory_package_no_generators(self):
        report_id = uuid.uuid4().hex
        bridge_empty = MarketPortfolioStressAuditComplianceBridge()
        result = bridge_empty.export_regulatory_package(report_id)
        self.assertFalse(result)

    def test_handle_stress_anomaly_success(self):
        anomaly_id = uuid.uuid4().hex
        score = random.uniform(0.0, 100.0)
        flagged = random.choice([True, False])

        anomaly_data = {
            "anomaly_id": anomaly_id,
            "score": score,
            "flagged": flagged
        }
        self.anomaly_detector.analyze_anomaly.return_value = anomaly_data
        dispatch_response = {"dispatched": True, "token": uuid.uuid4().hex}
        self.alert_dispatcher.dispatch.return_value = dispatch_response

        result = self.bridge.handle_stress_anomaly(anomaly_id)

        self.anomaly_detector.analyze_anomaly.assert_called_once_with(anomaly_id)
        self.alert_dispatcher.dispatch.assert_called_once_with({
            "anomaly_id": anomaly_id,
            "score": score,
            "flagged": flagged
        })
        self.assertEqual(result, dispatch_response)

    def test_handle_stress_anomaly_missing_components(self):
        anomaly_id = uuid.uuid4().hex
        bridge_empty = MarketPortfolioStressAuditComplianceBridge()
        result = bridge_empty.handle_stress_anomaly(anomaly_id)
        self.assertEqual(result, {"dispatched": False})

    def test_safely_execute_scenario_success(self):
        scenario_token = uuid.uuid4().hex
        result = self.bridge.safely_execute_scenario(scenario_token)

        self.scenario_executor.execute_scenario.assert_called_once_with(scenario_token)
        self.assertEqual(result, {"success": True})

    def test_safely_execute_scenario_exception(self):
        scenario_token = uuid.uuid4().hex
        error_message = uuid.uuid4().hex
        self.scenario_executor.execute_scenario.side_effect = Exception(error_message)

        result = self.bridge.safely_execute_scenario(scenario_token)

        self.scenario_executor.execute_scenario.assert_called_once_with(scenario_token)
        self.db_storage.log_error.assert_called_once_with(error_message)
        self.assertEqual(result, {"success": False, "error": error_message})

    def test_safely_execute_scenario_no_executor(self):
        scenario_token = uuid.uuid4().hex
        bridge_no_exec = MarketPortfolioStressAuditComplianceBridge()
        result = bridge_no_exec.safely_execute_scenario(scenario_token)
        self.assertEqual(result, {"success": True})

    def test_validate_allocation_policy_success(self):
        portfolio_uuid = uuid.uuid4().hex
        allocation_limit = random.randint(1000, 500000)
        allocation_result = {"allocated": True, "uuid": portfolio_uuid}
        validation_response = {"valid": True}

        self.allocator.calculate_optimal_allocation.return_value = allocation_result
        self.compliance_hub.validate_limits.return_value = validation_response

        result = self.bridge.validate_allocation_policy(portfolio_uuid, allocation_limit)

        self.allocator.calculate_optimal_allocation.assert_called_once_with(portfolio_uuid, allocation_limit)
        self.compliance_hub.validate_limits.assert_called_once_with(allocation_result)
        self.assertEqual(result, validation_response)

    def test_validate_allocation_policy_missing_deps(self):
        portfolio_uuid = uuid.uuid4().hex
        allocation_limit = random.randint(100, 9999)
        bridge_empty = MarketPortfolioStressAuditComplianceBridge()
        result = bridge_empty.validate_allocation_policy(portfolio_uuid, allocation_limit)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()