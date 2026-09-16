import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.incident_sla_mitigation_planner import (
    IncidentSLAMitigationPlanner,
    incident_sla_mitigation_planner
)

class TestIncidentSLAMitigationPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.inc_id = f"inc-{uuid.uuid4().hex[:8]}"
        self.tracker_id = uuid.uuid4().hex

    def test_generate_mitigation_plan_with_matching_breach(self):
        custom_step_1 = f"step_{uuid.uuid4().hex[:6]}"
        custom_step_2 = f"step_{uuid.uuid4().hex[:6]}"
        mock_breaches = [
            {"incident_id": uuid.uuid4().hex, "status": "WARNING"},
            {"incident_id": self.inc_id, "status": "BREACHED", "custom_steps": [custom_step_1, custom_step_2]}
        ]
        mock_tracker = {"tracker_id": self.tracker_id}

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_module:

            mock_predictor.get_predicted_breaches.return_value = mock_breaches
            mock_tracker_module.get_active_tracker.return_value = mock_tracker

            result = self.planner.generate_mitigation_plan(self.inc_id)

            self.assertEqual(result["incident_id"], self.inc_id)
            self.assertEqual(result["tracker_id"], self.tracker_id)
            self.assertIn(custom_step_1, result["steps"])
            self.assertIn(custom_step_2, result["steps"])

    def test_generate_mitigation_plan_fallback_to_default_tracker_and_steps(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_module:

            mock_predictor.get_predicted_breaches.return_value = []
            mock_tracker_module.get_active_tracker.return_value = None

            result = self.planner.generate_mitigation_plan(self.inc_id)

            self.assertEqual(result, {})

    def test_build_plan_for_incident_success(self):
        risk_key = f"risk_{uuid.uuid4().hex[:6]}"
        risk_val = random.randint(10, 100)
        tracker_key = f"detail_{uuid.uuid4().hex[:6]}"
        step_name = f"remedy_{uuid.uuid4().hex[:6]}"

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_module, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:

            mock_predictor.check_breach_risk.return_value = {risk_key: risk_val}
            mock_tracker_module.get_tracker_details.return_value = {tracker_key: True}
            mock_kb.find_remediation_steps.return_value = [step_name]

            res = self.planner.build_plan_for_incident(self.inc_id)

            self.assertEqual(res["incident_id"], self.inc_id)
            self.assertEqual(res["remediation_steps"], [step_name])
            self.assertEqual(res["risk_info"][risk_key], risk_val)
            self.assertTrue(res["tracker_details"][tracker_key])

    def test_build_plan_for_incident_default_remediation(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_module, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:

            mock_predictor.check_breach_risk.return_value = {}
            mock_tracker_module.get_tracker_details.return_value = {}
            mock_kb.find_remediation_steps.return_value = []

            res = self.planner.build_plan_for_incident(self.inc_id)

            self.assertEqual(res["remediation_steps"], ["DEFAULT_REMEDIATION_STEP"])

    def test_export_mitigation_report_custom_stream(self):
        random_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter") as mock_exporter:
            mock_exporter.export_stream.return_value = mock_stream

            stream_res = self.planner.export_mitigation_report()
            self.assertEqual(stream_res.read(), random_bytes)

    def test_export_mitigation_report_default_stream(self):
        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter") as mock_exporter:
            mock_exporter.export_stream.return_value = None

            stream_res = self.planner.export_mitigation_report()
            content = stream_res.read().decode('utf-8')
            self.assertIn("incident_id,status", content)

    def test_evaluate_and_mitigate_critical_urgency(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:

            mock_predictor.analyze_risk.return_value = {"urgency": "CRITICAL"}

            self.planner.evaluate_and_mitigate(self.inc_id)

            mock_escalation.trigger_escalation.assert_called_once_with(self.inc_id)

    def test_evaluate_and_mitigate_non_critical(self):
        urgency_level = random.choice(["LOW", "MEDIUM", "HIGH"])
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:

            mock_predictor.analyze_risk.return_value = {"urgency": urgency_level}

            self.planner.evaluate_and_mitigate(self.inc_id)

            mock_escalation.trigger_escalation.assert_not_called()

    def test_integration_wrapper_with_string_payload(self):
        payload_str = f"inc-str-{uuid.uuid4().hex[:8]}"
        res = incident_sla_mitigation_planner(payload_str)

        self.assertEqual(res["target_incident_id"], payload_str)
        self.assertIn("mitigation_plan_id", res)
        self.assertEqual(res["status"], "generated")
        self.assertIsInstance(res["remediation_steps"], list)

    def test_integration_wrapper_with_dict_payload(self):
        custom_step = f"hotfix_{uuid.uuid4().hex[:6]}"
        payload_dict = {
            "incident_id": self.inc_id,
            "prediction_payload": {
                "remediation_steps": [custom_step]
            }
        }
        res = incident_sla_mitigation_planner(payload_dict)

        self.assertEqual(res["target_incident_id"], self.inc_id)
        self.assertEqual(res["remediation_steps"], [custom_step])
        self.assertEqual(res["status"], "generated")

    def test_integration_wrapper_with_invalid_payload(self):
        res = incident_sla_mitigation_planner(None)

        self.assertTrue(res["target_incident_id"].startswith("inc-"))
        self.assertEqual(res["status"], "generated")