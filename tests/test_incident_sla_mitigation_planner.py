import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_sla_mitigation_planner import IncidentSLAMitigationPlanner

class TestIncidentSLAMitigationPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = IncidentSLAMitigationPlanner()
        self.random_incident_id = uuid.uuid4().hex
        self.random_tracker_id = uuid.uuid4().hex
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_remediation_step = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    def test_analyze_and_generate_plan_success(self):
        mock_predictor_data = {
            "incident_id": self.random_incident_id,
            "risk_score": round(random.uniform(0.75, 0.99), 2),
            "predicted_breach_in_minutes": random.randint(5, 60)
        }
        
        mock_tracker_data = {
            "tracker_id": self.random_tracker_id,
            "severity": self.random_severity,
            "current_status": "ACTIVE"
        }

        with patch('skills.incident_sla_mitigation_planner.incident_sla_breach_predictor') as mock_predictor, \
             patch('skills.incident_sla_mitigation_planner.incident_sla_tracker') as mock_tracker:

            mock_predictor.get_predicted_breaches.return_value = [mock_predictor_data]
            mock_tracker.get_active_tracker.return_value = mock_tracker_data

            plan = self.planner.generate_mitigation_plan(self.random_incident_id)

            self.assertIsNotNone(plan)
            self.assertEqual(plan["incident_id"], self.random_incident_id)
            self.assertEqual(plan["tracker_id"], self.random_tracker_id)
            self.assertIn("steps", plan)
            self.assertTrue(len(plan["steps"]) > 0)

    def test_mitigation_plan_contains_dynamic_remediation(self):
        incident_id = uuid.uuid4().hex
        custom_step = f"EXECUTE_FIX_{uuid.uuid4().hex[:8]}"

        with patch('skills.incident_sla_mitigation_planner.incident_sla_breach_predictor') as mock_predictor, \
             patch('skills.incident_sla_mitigation_planner.incident_sla_tracker') as mock_tracker, \
             patch('skills.incident_sla_mitigation_planner.incident_knowledge_base_searcher') as mock_kb:

            mock_predictor.check_breach_risk.return_value = {"risk": "HIGH"}
            mock_tracker.get_tracker_details.return_value = {"id": incident_id, "state": "OPEN"}
            mock_kb.find_remediation_steps.return_value = [custom_step]

            result_plan = self.planner.build_plan_for_incident(incident_id)

            self.assertIn(custom_step, result_plan["remediation_steps"])
            self.assertEqual(result_plan["incident_id"], incident_id)

    def test_handle_empty_predictor_data(self):
        dead_incident_id = uuid.uuid4().hex

        with patch('skills.incident_sla_mitigation_planner.incident_sla_breach_predictor') as mock_predictor, \
             patch('skills.incident_sla_mitigation_planner.incident_sla_tracker') as mock_tracker:

            mock_predictor.get_predicted_breaches.return_value = []
            mock_tracker.get_active_tracker.return_value = None

            plan = self.planner.generate_mitigation_plan(dead_incident_id)

            self.assertEqual(plan, {})

    def test_io_stream_handling_for_bulk_export(self):
        mock_stream_data = f"incident_id,status\n{self.random_incident_id},MITIGATED".encode('utf-8')
        fake_file = io.BytesIO(mock_stream_data)

        with patch('skills.incident_sla_mitigation_planner.recovery_report_exporter') as mock_exporter:
            mock_exporter.export_stream.return_value = fake_file

            exported_stream = self.planner.export_mitigation_report()
            content = exported_stream.read().decode('utf-8')

            self.assertIn(self.random_incident_id, content)
            self.assertIn("MITIGATED", content)

    def test_escalation_trigger_on_critical_risk(self):
        critical_incident_id = uuid.uuid4().hex

        with patch('skills.incident_sla_mitigation_planner.incident_sla_breach_predictor') as mock_predictor, \
             patch('skills.incident_sla_mitigation_planner.incident_auto_escalation_engine') as mock_escalation:

            mock_predictor.analyze_risk.return_value = {
                "incident_id": critical_incident_id,
                "urgency": "CRITICAL"
            }

            self.planner.evaluate_and_mitigate(critical_incident_id)

            mock_escalation.trigger_escalation.assert_called_once()
            args, _ = mock_escalation.trigger_escalation.call_args
            self.assertEqual(args[0], critical_incident_id)