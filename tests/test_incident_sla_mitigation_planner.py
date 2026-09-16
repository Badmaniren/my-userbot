import unittest
from unittest.mock import patch
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
        self.incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        self.tracker_id = uuid.uuid4().hex

    def test_generate_mitigation_plan_with_list_breaches(self):
        rand_step_1 = f"step_{uuid.uuid4().hex[:6]}"
        rand_step_2 = f"step_{uuid.uuid4().hex[:6]}"
        
        mock_breaches = [{
            "incident_id": self.incident_id,
            "risk_level": "HIGH"
        }]
        mock_tracker = {
            "tracker_id": self.tracker_id
        }

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_mod:
            
            mock_predictor.get_predicted_breaches.return_value = mock_breaches
            mock_tracker_mod.get_active_tracker.return_value = mock_tracker

            result = self.planner.generate_mitigation_plan(self.incident_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("tracker_id"), self.tracker_id)
            self.assertIn("steps", result)

    def test_generate_mitigation_plan_empty_fallback(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_mod:
            
            mock_predictor.get_predicted_breaches.return_value = []
            mock_tracker_mod.get_active_tracker.return_value = None

            result = self.planner.generate_mitigation_plan(self.incident_id)
            self.assertEqual(result, {})

    def test_build_plan_for_incident(self):
        rand_remediation = f"fix_{uuid.uuid4().hex[:6]}"
        mock_risk = {"risk": random.choice(["LOW", "MEDIUM", "HIGH"])}
        mock_details = {"details": uuid.uuid4().hex}
        mock_steps = [rand_remediation]

        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_mod, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_predictor.check_breach_risk.return_value = mock_risk
            mock_tracker_mod.get_tracker_details.return_value = mock_details
            mock_kb.find_remediation_steps.return_value = mock_steps

            result = self.planner.build_plan_for_incident(self.incident_id)

            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("remediation_steps"), mock_steps)
            self.assertEqual(result.get("risk_info"), mock_risk)
            self.assertEqual(result.get("tracker_details"), mock_details)

    def test_build_plan_for_incident_default_steps(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_sla_tracker") as mock_tracker_mod, \
             patch("skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher") as mock_kb:
            
            mock_predictor.check_breach_risk.return_value = {}
            mock_tracker_mod.get_tracker_details.return_value = {}
            mock_kb.find_remediation_steps.return_value = []

            result = self.planner.build_plan_for_incident(self.incident_id)

            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertIn("DEFAULT_REMEDIATION_STEP", result.get("remediation_steps"))

    def test_export_mitigation_report(self):
        expected_bytes = f"id,status\n{self.incident_id},OK".encode("utf-8")
        mock_stream = io.BytesIO(expected_bytes)

        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter") as mock_exporter:
            mock_exporter.export_stream.return_value = mock_stream

            stream_res = self.planner.export_mitigation_report()
            self.assertIsInstance(stream_res, io.BytesIO)
            self.assertEqual(stream_res.read(), expected_bytes)

    def test_export_mitigation_report_fallback(self):
        with patch("skills.incident_sla_mitigation_planner.recovery_report_exporter", None):
            stream_res = self.planner.export_mitigation_report()
            self.assertIsInstance(stream_res, io.BytesIO)
            self.assertTrue(len(stream_res.read()) > 0)

    def test_evaluate_and_mitigate_critical_urgency(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:
            
            mock_predictor.analyze_risk.return_value = {"urgency": "CRITICAL"}

            self.planner.evaluate_and_mitigate(self.incident_id)
            mock_escalation.trigger_escalation.assert_called_once_with(self.incident_id)

    def test_evaluate_and_mitigate_non_critical(self):
        with patch("skills.incident_sla_mitigation_planner.incident_sla_breach_predictor") as mock_predictor, \
             patch("skills.incident_sla_mitigation_planner.incident_auto_escalation_engine") as mock_escalation:
            
            mock_predictor.analyze_risk.return_value = {"urgency": random.choice(["LOW", "MEDIUM", "NORMAL"])}

            self.planner.evaluate_and_mitigate(self.incident_id)
            mock_escalation.trigger_escalation.assert_not_called()

    def test_incident_sla_mitigation_planner_functional_string_payload(self):
        res = incident_sla_mitigation_planner(self.incident_id)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("target_incident_id"), self.incident_id)
        self.assertEqual(res.get("status"), "generated")
        self.assertIn("mitigation_plan_id", res)

    def test_incident_sla_mitigation_planner_functional_dict_payload(self):
        rand_step = f"custom_step_{uuid.uuid4().hex[:6]}"
        payload = {
            "incident_id": self.incident_id,
            "prediction_payload": {
                "remediation_steps": [rand_step]
            }
        }

        res = incident_sla_mitigation_planner(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("target_incident_id"), self.incident_id)
        self.assertIn(rand_step, res.get("remediation_steps"))

    def test_incident_sla_mitigation_planner_invalid_payload(self):
        res = incident_sla_mitigation_planner(12345)
        self.assertIsInstance(res, dict)
        self.assertIsNotNone(res.get("target_incident_id"))
        self.assertEqual(res.get("status"), "generated")


if __name__ == "__main__":
    unittest.main()