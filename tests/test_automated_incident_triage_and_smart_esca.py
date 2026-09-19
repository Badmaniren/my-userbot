import unittest
from skills.automated_incident_triage_and_smart_esca import (
    IncidentSeverityEvaluator,
    IncidentAutoEscalationEngine,
    IncidentTriagePipeline,
    IncidentEscalationTriageBridge,
    automated_incident_triage_and_smart_esca
)


class TestAutomatedIncidentTriageAndSmartEsca(unittest.TestCase):

    def setUp(self):
        self.evaluator = IncidentSeverityEvaluator()
        self.engine = IncidentAutoEscalationEngine()
        self.pipeline = IncidentTriagePipeline()
        self.bridge = IncidentEscalationTriageBridge()

    def test_evaluator_dict_payload(self):
        critical_payload = {"incident_id": "INC-1", "severity_score": 9.2}
        self.assertEqual(self.evaluator.evaluate(critical_payload), "CRITICAL")

        high_payload = {"incident_id": "INC-2", "severity_score": 7.5}
        self.assertEqual(self.evaluator.evaluate(high_payload), "HIGH")

        medium_payload = {"incident_id": "INC-3", "severity_score": 4.0}
        self.assertEqual(self.evaluator.evaluate(medium_payload), "MEDIUM")

        low_payload = {"incident_id": "INC-4", "severity_score": 1.5}
        self.assertEqual(self.evaluator.evaluate(low_payload), "LOW")

    def test_engine_determine_escalation(self):
        decision_crit = self.engine.determine_escalation({"incident_id": "INC-1"}, "CRITICAL")
        self.assertEqual(decision_crit, "ESCALATE_IMMEDIATELY")

        decision_med = self.engine.determine_escalation({"incident_id": "INC-2"}, "MEDIUM")
        self.assertEqual(decision_med, "AUTOMATED_QUEUE")

        decision_low = self.engine.determine_escalation({"incident_id": "INC-3"}, "LOW")
        self.assertEqual(decision_low, "LOG_AND_MONITOR")

    def test_pipeline_run_pipeline(self):
        res = self.pipeline.run_pipeline({"incident_id": "INC-100", "severity_score": 8.5})
        self.assertEqual(res["incident_id"], "INC-100")
        self.assertEqual(res["status"], "TRIAGED")
        self.assertEqual(res["severity"], "CRITICAL")

    def test_bridge_bridge_triage_and_escalation(self):
        triage_res = {"incident_id": "INC-100", "status": "TRIAGED", "severity": "CRITICAL"}
        bridge_res = self.bridge.bridge_triage_and_escalation(triage_res, "ESCALATE_IMMEDIATELY")
        self.assertEqual(bridge_res["bridge_id"], "bridge_INC-100")
        self.assertEqual(bridge_res["incident_id"], "INC-100")
        self.assertEqual(bridge_res["action"], "ACTION_ESCALATE_IMMEDIATELY")

    def test_top_level_function(self):
        res = automated_incident_triage_and_smart_esca({"incident_id": "INC-200", "severity_score": 9.0})
        self.assertEqual(res["bridge_id"], "bridge_INC-200")
        self.assertIn("action", res)


if __name__ == "__main__":
    unittest.main()
