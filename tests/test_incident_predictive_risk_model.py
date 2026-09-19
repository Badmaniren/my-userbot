import unittest
from unittest.mock import patch
import uuid
import io

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
