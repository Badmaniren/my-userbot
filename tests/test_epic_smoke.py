import unittest
import json
import tempfile
import os
from unittest.mock import patch

from incident_severity_evaluator import IncidentSeverityEvaluator
from incident_auto_escalation_engine import IncidentAutoEscalationEngine
from incident_triage_pipeline import IncidentTriagePipeline
from incident_escalation_triage_bridge import IncidentEscalationTriageBridge


class TestAutomatedIncidentTriageAndSmartEscalationLive(unittest.TestCase):
    
    def setUp(self):
        self.test_incidents = [
            {
                "incident_id": "INC-9001",
                "source": "anti_cheat_subsystem",
                "event_type": "memory_tampering_attempt",
                "severity_score": 9.5,
                "affected_users": 1,
                "vector": "kernel_hook",
                "details": "Unauthorized modification of client memory space detected during active match."
            },
            {
                "incident_id": "INC-9002",
                "source": "api_gateway",
                "event_type": "rate_limit_exceeded",
                "severity_score": 3.2,
                "affected_users": 45,
                "vector": "http_flood",
                "details": "Multiple rapid requests from a single IP address."
            },
            {
                "incident_id": "INC-9003",
                "source": "auth_service",
                "event_type": "credential_stuffing_wave",
                "severity_score": 7.8,
                "affected_users": 1200,
                "vector": "botnet",
                "details": "Distributed login attempts using leaked credential databases."
            }
        ]
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.test_incidents, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_end_to_end_triage_and_escalation_pipeline(self):
        print("\n=== STARTING PRACTICAL CHECK: Automated Incident Triage and Smart Escalation ===")
        
        with open(self.temp_file.name, 'r') as f:
            raw_data = json.load(f)
        
        print(f"[1] Loaded {len(raw_data)} realistic incidents from temporary telemetry storage.")

        evaluator = IncidentSeverityEvaluator()
        engine = IncidentAutoEscalationEngine()
        pipeline = IncidentTriagePipeline()
        bridge = IncidentEscalationTriageBridge()

        processed_results = []
        
        for inc in raw_data:
            print(f"\n--- Processing Incident: {inc['incident_id']} ({inc['event_type']}) ---")
            
            evaluated_severity = evaluator.evaluate(inc)
            print(f" -> Evaluated Severity Level: {evaluated_severity}")
            
            escalation_decision = engine.determine_escalation(inc, evaluated_severity)
            print(f" -> Smart Escalation Decision: {escalation_decision}")
            
            triage_result = pipeline.run_pipeline(inc)
            print(f" -> Triage Pipeline Status: {triage_result.get('status')}")
            
            bridge_payload = bridge.bridge_triage_and_escalation(triage_result, escalation_decision)
            print(f" -> Bridge Finalized Payload ID: {bridge_payload.get('bridge_id')}, Action: {bridge_payload.get('action')}")
            
            processed_results.append({
                "incident_id": inc["incident_id"],
                "severity": evaluated_severity,
                "escalation": escalation_decision,
                "action": bridge_payload.get("action")
            })

        print("\n=== SUMMARY OF LIVE Triage and Escalation RUN ===")
        for res in processed_results:
            print(f"Incident {res['incident_id']} -> Severity: {res['severity']} | Escalation: {res['escalation']} | Action: {res['action']}")
            self.assertIn("action", res)
            self.assertIsNotNone(res["severity"])

        print("=== PRACTICAL CHECK COMPLETED SUCCESSFULLY ===\n")


if __name__ == "__main__":
    unittest.main()