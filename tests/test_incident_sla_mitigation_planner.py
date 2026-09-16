import io
import uuid
import random
import unittest
from unittest.mock import patch, MagicMock

from skills.incident_sla_mitigation_planner import (
    IncidentSLAMitigationPlanner,
    incident_sla_mitigation_planner
)


class TestIncidentSLAMitigationPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.random_incident_id = f"inc-{uuid.uuid4().hex}"
        self.random_tracker_id = f"trk-{uuid.uuid4().hex}"

    def test_generate_mitigation_plan_with_list_breaches_matched(self):
        rnd_step = f"step-{uuid.uuid4().hex}"
        mock_breaches = [
            {"incident_id": self.random_incident_id, "detail": uuid.uuid4().hex}
        ]
        mock_tracker = {"tracker_id": self.random_tracker_id}

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_trk:
            
            mock_pred.get_predicted_breaches.return_value = mock_breaches
            mock_trk.get_active_tracker.return_value = mock_tracker

            result = self.planner.generate_mitigation_plan(self.random_incident_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.random_incident_id)
            self.assertEqual(result.get("tracker_id"), self.random_tracker_id)
            self.assertIn("steps", result)

    def test_generate_mitigation_plan_fallback_unstructured(self):
        mock_breaches = [{"unrelated_key": uuid.uuid4().hex}]
        
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_trk:
            
            mock_pred.get_predicted_breaches.return_value = mock_breaches
            mock_trk.get_active_tracker.return_value = None

            result = self.planner.generate_mitigation_plan(self.random_incident_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.random_incident_id)
            self.assertIsInstance(result.get("tracker_id"), str)

    def test_generate_mitigation_plan_empty_returns_empty(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_trk:
            
            mock_pred.get_predicted_breaches.return_value = []
            mock_trk.get_active_tracker.return_value = None

            result = self.planner.generate_mitigation_plan(self.random_incident_id)

            self.assertEqual(result, {})

    def test_build_plan_for_incident_custom_remediation(self):
        rnd_risk_key = uuid.uuid4().hex
        rnd_risk_val = uuid.uuid4().hex
        rnd_step = uuid.uuid4().hex

        mock_risk = {rnd_risk_key: rnd_risk_val}
        mock_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_steps = [rnd_step]

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_trk, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_pred.check_breach_risk.return_value = mock_risk
            mock_trk.get_tracker_details.return_value = mock_details
            mock_kb.find_remediation_steps.return_value = mock_steps

            result = self.planner.build_plan_for_incident(self.random_incident_id)

            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["remediation_steps"], mock_steps)
            self.assertEqual(result["risk_info"], mock_risk)
            self.assertEqual(result["tracker_details"], mock_details)

    def test_build_plan_for_incident_default_remediation(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_trk, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_pred.check_breach_risk.return_value = {}
            mock_trk.get_tracker_details.return_value = {}
            mock_kb.find_remediation_steps.return_value = []

            result = self.planner.build_plan_for_incident(self.random_incident_id)

            self.assertEqual(result["remediation_steps"], ["DEFAULT_REMEDIATION_STEP"])

    def test_export_mitigation_report_stream(self):
        rnd_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(rnd_bytes)

        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter") as mock_exp:
            mock_exp.export_stream.return_value = mock_stream

            stream_result = self.planner.export_mitigation_report()

            self.assertIsInstance(stream_result, io.BytesIO)
            self.assertEqual(stream_result.read(), rnd_bytes)

    def test_export_mitigation_report_fallback(self):
        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter", None):
            stream_result = self.planner.export_mitigation_report()
            self.assertIsInstance(stream_result, io.BytesIO)
            self.assertIn(b"incident_id", stream_result.read())

    def test_evaluate_and_mitigate_critical_urgency(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_esc:
            
            mock_pred.analyze_risk.return_value = {"urgency": "CRITICAL"}

            self.planner.evaluate_and_mitigate(self.random_incident_id)

            mock_esc.trigger_escalation.assert_called_once_with(self.random_incident_id)

    def test_evaluate_and_mitigate_non_critical(self):
        random_urgency = random.choice(["LOW", "MEDIUM", "HIGH", uuid.uuid4().hex])

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_pred, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_esc:
            
            mock_pred.analyze_risk.return_value = {"urgency": random_urgency}

            self.planner.evaluate_and_mitigate(self.random_incident_id)

            mock_esc.trigger_escalation.assert_not_called()

    def test_functional_entrypoint_with_string_payload(self):
        result = incident_sla_mitigation_planner(self.random_incident_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_incident_id"), self.random_incident_id)
        self.assertEqual(result.get("status"), "generated")
        self.assertIn("mitigation_plan_id", result)

    def test_functional_entrypoint_with_dict_payload_custom_steps(self):
        rnd_custom_step = uuid.uuid4().hex
        payload = {
            "incident_id": self.random_incident_id,
            "prediction_payload": {
                "remediation_steps": [rnd_custom_step]
            }
        }

        result = incident_sla_mitigation_planner(payload)

        self.assertEqual(result.get("target_incident_id"), self.random_incident_id)
        self.assertEqual(result.get("remediation_steps"), [rnd_custom_step])

    def test_functional_entrypoint_with_invalid_payload(self):
        result = incident_sla_mitigation_planner(12345)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("target_incident_id").startswith("inc-"))
        self.assertEqual(result.get("status"), "generated")