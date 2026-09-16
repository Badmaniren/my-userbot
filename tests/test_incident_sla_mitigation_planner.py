import io
import random
import unittest
from unittest.mock import patch, MagicMock
import uuid

from skills.incident_sla_mitigation_planner import (
    IncidentSLAMitigationPlanner,
    incident_sla_mitigation_planner,
)


class TestIncidentSLAMitigationPlannerUnit(unittest.TestCase):

    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.incident_id = f"inc-{uuid.uuid4().hex}"
        self.tracker_id = f"trk-{uuid.uuid4().hex}"

    def test_generate_mitigation_plan_with_list_breaches(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker:
            
            mock_predictor.get_predicted_breaches.return_value = [
                {"incident_id": self.incident_id, "status": "BREACHED"}
            ]
            mock_tracker.get_active_tracker.return_value = {
                "tracker_id": self.tracker_id
            }

            result = self.planner.generate_mitigation_plan(self.incident_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("tracker_id"), self.tracker_id)
            self.assertIn("steps", result)
            self.assertTrue(len(result["steps"]) > 0)

    def test_generate_mitigation_plan_empty_data(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker:
            
            mock_predictor.get_predicted_breaches.return_value = []
            mock_tracker.get_active_tracker.return_value = None

            result = self.planner.generate_mitigation_plan(self.incident_id)
            self.assertEqual(result, {})

    def test_build_plan_for_incident_with_remediation(self):
        risk_level = random.choice(["HIGH", "CRITICAL", "MEDIUM"])
        step_name = f"step-{uuid.uuid4().hex}"

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_predictor.check_breach_risk.return_value = {"level": risk_level}
            mock_tracker.get_tracker_details.return_value = {"status": "ACTIVE"}
            mock_kb.find_remediation_steps.return_value = [step_name]

            result = self.planner.build_plan_for_incident(self.incident_id)

            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertIn(step_name, result.get("remediation_steps", []))
            self.assertEqual(result.get("risk_info", {}).get("level"), risk_level)
            self.assertEqual(result.get("tracker_details", {}).get("status"), "ACTIVE")

    def test_build_plan_for_incident_default_steps(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_predictor.check_breach_risk.return_value = {}
            mock_tracker.get_tracker_details.return_value = {}
            mock_kb.find_remediation_steps.return_value = []

            result = self.planner.build_plan_for_incident(self.incident_id)

            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertIn("DEFAULT_REMEDIATION_STEP", result.get("remediation_steps", []))

    def test_export_mitigation_report(self):
        random_bytes = f"incident_id,status\n{self.incident_id},MITIGATED".encode("utf-8")
        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter") as mock_exporter:
            mock_exporter.export_stream.return_value = io.BytesIO(random_bytes)

            stream = self.planner.export_mitigation_report()
            self.assertIsInstance(stream, io.BytesIO)
            content = stream.read().decode("utf-8")
            self.assertIn(self.incident_id, content)

    def test_evaluate_and_mitigate_critical(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:
            
            mock_predictor.analyze_risk.return_value = {"urgency": "CRITICAL"}

            self.planner.evaluate_and_mitigate(self.incident_id)
            mock_escalation.trigger_escalation.assert_called_once_with(self.incident_id)

    def test_evaluate_and_mitigate_non_critical(self):
        urgency = random.choice(["LOW", "MEDIUM", "WARNING"])
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:
            
            mock_predictor.analyze_risk.return_value = {"urgency": urgency}

            self.planner.evaluate_and_mitigate(self.incident_id)
            mock_escalation.trigger_escalation.assert_not_called()

    def test_incident_sla_mitigation_planner_function_with_string(self):
        result = incident_sla_mitigation_planner(self.incident_id)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), self.incident_id)
        self.assertEqual(result.get("status"), "generated")
        self.assertIn("mitigation_plan_id", result)

    def test_incident_sla_mitigation_planner_function_with_dict(self):
        custom_step = f"fix-{uuid.uuid4().hex}"
        payload = {
            "incident_id": self.incident_id,
            "prediction_payload": {
                "remediation_steps": [custom_step]
            }
        }
        result = incident_sla_mitigation_planner(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), self.incident_id)
        self.assertIn(custom_step, result.get("remediation_steps", []))

    def test_incident_sla_mitigation_planner_function_with_invalid(self):
        result = incident_sla_mitigation_planner(12345)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("target_incident_id").startswith("inc-"))


if __name__ == "__main__":
    unittest.main()