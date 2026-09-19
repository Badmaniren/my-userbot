import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.predictive_patch_pipeline import (
    PredictivePatchPipeline,
    PredictivePatchPipelineError
)

class TestPredictivePatchPipeline(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.package_name = f"pkg_{uuid.uuid4().hex[:8]}"
        self.version = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        self.stream_data = f"stream_{uuid.uuid4().hex}".encode('utf-8')
        self.path = f"/tmp/{uuid.uuid4().hex}.json"
        self.incident_data = {"incident_id": uuid.uuid4().hex, "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])}
        self.audit_summary = {"audit_score": random.uniform(50.0, 100.0)}
        self.metrics = {"latency_ms": random.randint(10, 500)}
        self.dashboard_format = random.choice(["json", "html", "pdf"])
        self.incidents_list = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        self.patches_list = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        self.report_path = f"/reports/{uuid.uuid4().hex}.rpt"
        self.dashboard_path = f"/dashboards/{uuid.uuid4().hex}.dash"

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_pipeline_initialization(self, mock_applier_cls, mock_bridge_cls):
        bridge_instance = mock_bridge_cls.return_value
        applier_instance = mock_applier_cls.return_value

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=applier_instance)

        self.assertEqual(pipeline.bridge, bridge_instance)
        self.assertEqual(pipeline.applier, applier_instance)

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_run_comprehensive_predictive_patch_cycle(self, mock_applier_cls, mock_bridge_cls):
        expected_telemetry_result = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_patch_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        bridge_instance = mock_bridge_cls.return_value
        bridge_instance.run_vulnerability_telemetry_cycle.return_value = expected_telemetry_result

        applier_instance = mock_applier_cls.return_value
        applier_instance.run_preventive_cycle.return_value = expected_patch_result

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=applier_instance)
        result = pipeline.run_comprehensive_predictive_patch_cycle(
            module_name=self.module_name,
            package_name=self.package_name,
            version=self.version,
            incident_data=self.incident_data,
            audit_summary=self.audit_summary,
            metrics=self.metrics,
            dashboard_format=self.dashboard_format,
            incidents_list=self.incidents_list,
            patches_list=self.patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        bridge_instance.run_vulnerability_telemetry_cycle.assert_called_once_with(
            module_name=self.module_name,
            package_name=self.package_name,
            version=self.version,
            incident_data=self.incident_data,
            audit_summary=self.audit_summary,
            metrics=self.metrics,
            dashboard_format=self.dashboard_format,
            incidents_list=self.incidents_list,
            patches_list=self.patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )
        applier_instance.run_preventive_cycle.assert_called_once_with(self.module_name)

        self.assertIn("telemetry_cycle", result)
        self.assertIn("preventive_cycle", result)
        self.assertEqual(result["telemetry_cycle"], expected_telemetry_result)
        self.assertEqual(result["preventive_cycle"], expected_patch_result)

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_process_stream_and_apply_patches(self, mock_applier_cls, mock_bridge_cls):
        expected_stream_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_prevent_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        bridge_instance = mock_bridge_cls.return_value
        bridge_instance.process_stream_and_telemetry.return_value = expected_stream_result

        applier_instance = mock_applier_cls.return_value
        applier_instance.prevent_failures_from_stream.return_value = expected_prevent_result

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=applier_instance)

        stream_io = io.BytesIO(self.stream_data)
        result = pipeline.process_stream_and_apply_patches(self.module_name, stream_io, self.path)

        bridge_instance.process_stream_and_telemetry.assert_called_once_with(stream_io, self.path)
        applier_instance.prevent_failures_from_stream.assert_called_once_with(self.module_name, stream_io)

        self.assertEqual(result["stream_processing"], expected_stream_result)
        self.assertEqual(result["preventive_stream_result"], expected_prevent_result)

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_execute_full_pipeline_flow(self, mock_applier_cls, mock_bridge_cls):
        expected_bridge_output = {uuid.uuid4().hex: random.choice([True, False])}
        expected_apply_output = {uuid.uuid4().hex: random.randint(0, 5)}

        bridge_instance = mock_bridge_cls.return_value
        bridge_instance.execute_bridge_pipeline.return_value = expected_bridge_output

        applier_instance = mock_applier_cls.return_value
        applier_instance.apply_preventive_patches.return_value = expected_apply_output

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=applier_instance)

        result = pipeline.execute_full_pipeline_flow(
            module_name=self.module_name,
            incident_data=self.incident_data,
            audit_summary=self.audit_summary,
            metrics=self.metrics,
            dashboard_format=self.dashboard_format,
            incidents_list=self.incidents_list,
            patches_list=self.patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        bridge_instance.execute_bridge_pipeline.assert_called_once()
        applier_instance.apply_preventive_patches.assert_called_once_with(self.module_name)

        self.assertEqual(result["bridge_pipeline"], expected_bridge_output)
        self.assertEqual(result["apply_preventive_patches"], expected_apply_output)

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_pipeline_exception_handling(self, mock_applier_cls, mock_bridge_cls):
        bridge_instance = mock_bridge_cls.return_value
        bridge_instance.run_vulnerability_telemetry_cycle.side_effect = Exception(f"Error {uuid.uuid4().hex}")

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=mock_applier_cls.return_value)

        with self.assertRaises(PredictivePatchPipelineError):
            pipeline.run_comprehensive_predictive_patch_cycle(
                module_name=self.module_name,
                package_name=self.package_name,
                version=self.version,
                incident_data=self.incident_data,
                audit_summary=self.audit_summary,
                metrics=self.metrics,
                dashboard_format=self.dashboard_format,
                incidents_list=self.incidents_list,
                patches_list=self.patches_list,
                report_path=self.report_path,
                dashboard_path=self.dashboard_path
            )

    @patch('skills.predictive_patch_pipeline.PredictiveVulnerabilityTelemetryBridge')
    @patch('skills.predictive_patch_pipeline.PreventivePatchApplier')
    def test_export_and_apply_pipeline(self, mock_applier_cls, mock_bridge_cls):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_process_output = {uuid.uuid4().hex: random.random()}

        bridge_instance = mock_bridge_cls.return_value
        applier_instance = mock_applier_cls.return_value
        applier_instance.process_module.return_value = expected_process_output

        pipeline = PredictivePatchPipeline(bridge=bridge_instance, applier=applier_instance)
        result = pipeline.export_and_apply_pipeline(payload, self.path, self.module_name)

        bridge_instance.export_risk_and_vulnerability_report.assert_called_once_with(payload, self.path)
        applier_instance.process_module.assert_called_once_with(self.module_name)

        self.assertEqual(result["process_module"], expected_process_output)
        self.assertIn("report_exported", result)
        self.assertTrue(result["report_exported"])

if __name__ == '__main__':
    unittest.main()