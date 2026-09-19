import unittest
from unittest.mock import patch
import uuid
import random
import io
import sys
from types import ModuleType

def _create_dummy_module(name):
    mod = ModuleType(name)
    if name == 'skills.system_health_aggregator':
        mod.system_health_aggregator = object()
    elif name == 'skills.incident_trend_analyzer':
        mod.incident_trend_analyzer = object()
    elif name == 'skills.incident_severity_evaluator':
        mod.incident_severity_evaluator = object()
    elif name == 'skills.dependency_audit_reporter':
        mod.dependency_audit_reporter = type('obj', (object,), {'generate_report': lambda *a, **kw: None})()
    elif name == 'skills.dependency_vulnerability_assessor':
        mod.dependency_vulnerability_assessor = type('obj', (object,), {'assess': lambda *a, **kw: None})()
    elif name == 'skills.pypi_client':
        mod.pypi_client = object()
    elif name == 'skills.auto_patch_pipeline':
        mod.auto_patch_pipeline = type('obj', (object,), {'execute': lambda *a, **kw: None})()
    elif name == 'skills.incident_aggregator':
        mod.incident_aggregator = object()
    elif name == 'skills.system_risk_evaluator':
        mod.system_risk_evaluator = object()
    elif name == 'skills.incident_auto_escalation_engine':
        mod.incident_auto_escalation_engine = type('obj', (object,), {'evaluate_trigger': lambda *a, **kw: None})()
    elif name == 'skills.incident_auto_recovery_dispatcher':
        mod.incident_auto_recovery_dispatcher = type('obj', (object,), {'dispatch': lambda *a, **kw: None})()
    elif name == 'skills.telemetry_processor':
        mod.telemetry_processor = type('obj', (object,), {'process': lambda *a, **kw: None})()
    elif name == 'skills.telemetry_anomaly_evaluator_core':
        mod.telemetry_anomaly_evaluator_core = type('obj', (object,), {'detect': lambda *a, **kw: None})()
    elif name == 'skills.system_health_telemetry_collector':
        mod.system_health_telemetry_collector = object()
    elif name == 'skills.vulnerability_patch_orchestrator':
        mod.vulnerability_patch_orchestrator = type('obj', (object,), {'orchestrate': lambda *a, **kw: None})()
    elif name == 'skills.patch_validator':
        mod.patch_validator = type('obj', (object,), {'validate': lambda *a, **kw: None})()
    elif name == 'skills.patch_scheduler':
        mod.patch_scheduler = object()
    return mod

modules_to_mock = [
    'skills.system_health_aggregator',
    'skills.incident_trend_analyzer',
    'skills.incident_severity_evaluator',
    'skills.dependency_audit_reporter',
    'skills.dependency_vulnerability_assessor',
    'skills.pypi_client',
    'skills.auto_patch_pipeline',
    'skills.incident_aggregator',
    'skills.system_risk_evaluator',
    'skills.incident_auto_escalation_engine',
    'skills.incident_auto_recovery_dispatcher',
    'skills.telemetry_processor',
    'skills.telemetry_anomaly_evaluator_core',
    'skills.system_health_telemetry_collector',
    'skills.vulnerability_patch_orchestrator',
    'skills.patch_validator',
    'skills.patch_scheduler'
]

for m in modules_to_mock:
    if m not in sys.modules:
        sys.modules[m] = _create_dummy_module(m)

from skills.incident_predictive_risk_model import start_new, incident_predictive_risk_model

class TestIncidentPredictiveRiskModel(unittest.TestCase):

    def test_start_new_structure(self):
        rand_arg = uuid.uuid4().hex
        res = start_new(rand_arg)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("metric_id", res)
        self.assertIn("value", res)
        self.assertIsInstance(res["metric_id"], str)
        self.assertIsInstance(res["value"], float)

    def test_incident_predictive_risk_model_execution(self):
        sys_id = f"sys-{uuid.uuid4().hex}"
        inp = {"system_id": sys_id}
        
        mock_file_data = io.StringIO()
        with patch("builtins.open", return_value=mock_file_data) as mock_open:
            result = incident_predictive_risk_model(inp)
            self.assertEqual(result["target_system_id"], sys_id)
            self.assertIn("risk_assessment_id", result)
            self.assertIn("predicted_risk_score", result)
            self.assertEqual(result["status"], "success")
            mock_open.assert_called_once()

    def test_incident_predictive_risk_model_random_system_id(self):
        inp = {}
        with patch("builtins.open", create=True):
            result = incident_predictive_risk_model(inp)
            self.assertTrue(result["target_system_id"].startswith("sys-"))
            self.assertGreaterEqual(result["predicted_risk_score"], 0.0)
            self.assertLessEqual(result["predicted_risk_score"], 100.0)

    def test_start_new_invokes_dependencies(self):
        with patch('skills.dependency_audit_reporter.dependency_audit_reporter.generate_report') as mock_dep_audit, \
             patch('skills.auto_patch_pipeline.auto_patch_pipeline.execute') as mock_auto_patch:
            
            res = start_new(uuid.uuid4().hex, option=uuid.uuid4().hex)
            self.assertEqual(res["status"], "success")
            mock_dep_audit.assert_called_once()
            mock_auto_patch.assert_called_once()

if __name__ == '__main__':
    unittest.main()