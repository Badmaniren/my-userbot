import unittest
import os
import tempfile
import uuid
import random

from skills.predictive_vulnerability_telemetry_bridge import (
    PredictiveVulnerabilityTelemetryBridge,
)
from skills.preventive_patch_applier import (
    PreventivePatchApplier,
)
import skills.predictive_patch_pipeline as ppp_module


class TestPredictivePatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.unique_id = uuid.uuid4().hex[:8]
        self.module_name = f"mod_{self.unique_id}"
        self.package_name = f"pkg_{self.unique_id}"
        self.version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        self.report_path = os.path.join(self.test_dir.name, f"vuln_report_{self.unique_id}.json")
        self.dashboard_path = os.path.join(self.test_dir.name, f"dashboard_{self.unique_id}.html")

        self.incident_data = {
            "incident_id": f"inc-{uuid.uuid4().hex[:6]}",
            "severity": random.choice(["HIGH", "CRITICAL", "MEDIUM"]),
            "status": "DETECTED",
        }
        self.audit_summary = {
            "auditor": f"sec_agent_{self.unique_id}",
            "findings_count": random.randint(1, 5),
            "compliance_score": round(random.uniform(0.7, 0.99), 2),
        }
        self.metrics = {
            "cpu_usage": round(random.uniform(10.0, 95.0), 2),
            "memory_usage": round(random.uniform(100.0, 4096.0), 2),
            "risk_score": round(random.uniform(0.1, 1.0), 2),
        }
        self.dashboard_format = "html"
        self.incidents_list = [self.incident_data]
        self.patches_list = [
            {
                "patch_id": f"patch-{uuid.uuid4().hex[:6]}",
                "target_module": self.module_name,
                "action": "upgrade_lib",
            }
        ]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_composition_and_execution(self):
        pipeline = None
        if hasattr(ppp_module, "PredictivePatchPipeline"):
            pipeline = ppp_module.PredictivePatchPipeline()
        elif hasattr(ppp_module, "predictive_patch_pipeline"):
            pipeline = ppp_module.predictive_patch_pipeline

        self.assertIsNotNone(
            pipeline,
            "skills.predictive_patch_pipeline must define PredictivePatchPipeline or predictive_patch_pipeline",
        )

        pipeline_callable = None
        for method_name in [
            "run",
            "execute",
            "run_pipeline",
            "execute_pipeline",
            "run_cycle",
            "process",
        ]:
            if hasattr(pipeline, method_name) and callable(getattr(pipeline, method_name)):
                pipeline_callable = getattr(pipeline, method_name)
                break

        if pipeline_callable is None and callable(pipeline):
            pipeline_callable = pipeline

        self.assertIsNotNone(
            pipeline_callable,
            "Could not find an executable pipeline method on PredictivePatchPipeline",
        )

        kwargs_candidate = {
            "module_name": self.module_name,
            "package_name": self.package_name,
            "version": self.version,
            "incident_data": self.incident_data,
            "audit_summary": self.audit_summary,
            "metrics": self.metrics,
            "dashboard_format": self.dashboard_format,
            "incidents_list": self.incidents_list,
            "patches_list": self.patches_list,
            "report_path": self.report_path,
            "dashboard_path": self.dashboard_path,
        }

        try:
            result = pipeline_callable(**kwargs_candidate)
        except TypeError:
            try:
                result = pipeline_callable(
                    self.module_name,
                    self.package_name,
                    self.version,
                    self.incident_data,
                    self.audit_summary,
                    self.metrics,
                    self.dashboard_format,
                    self.incidents_list,
                    self.patches_list,
                    self.report_path,
                    self.dashboard_path,
                )
            except TypeError:
                result = pipeline_callable(self.module_name)

        self.assertIsNotNone(result, "Pipeline execution returned None")
        if isinstance(result, dict):
            matched_module = (
                result.get("module_name")
                or result.get("module")
                or (result.get("telemetry", {}).get("module_name") if isinstance(result.get("telemetry"), dict) else None)
                or (result.get("patches", {}).get("module_name") if isinstance(result.get("patches"), dict) else None)
            )
            if matched_module is not None:
                self.assertEqual(matched_module, self.module_name)

    def test_pipeline_uses_both_required_skills(self):
        source_bridge_found = False
        source_applier_found = False

        for attr_name in dir(ppp_module):
            attr = getattr(ppp_module, attr_name)
            if attr is PredictiveVulnerabilityTelemetryBridge or (
                isinstance(attr, type) and issubclass(attr, PredictiveVulnerabilityTelemetryBridge)
            ):
                source_bridge_found = True
            if attr is PreventivePatchApplier or (
                isinstance(attr, type) and issubclass(attr, PreventivePatchApplier)
            ):
                source_applier_found = True

        if not (source_bridge_found and source_applier_found):
            pipeline_cls = getattr(ppp_module, "PredictivePatchPipeline", None)
            if pipeline_cls:
                instance = pipeline_cls()
                for field in dir(instance):
                    val = getattr(instance, field)
                    if isinstance(val, PredictiveVulnerabilityTelemetryBridge):
                        source_bridge_found = True
                    if isinstance(val, PreventivePatchApplier):
                        source_applier_found = True

        self.assertTrue(
            source_bridge_found,
            "PredictivePatchPipeline must import and use PredictiveVulnerabilityTelemetryBridge",
        )
        self.assertTrue(
            source_applier_found,
            "PredictivePatchPipeline must import and use PreventivePatchApplier",
        )


if __name__ == "__main__":
    unittest.main()