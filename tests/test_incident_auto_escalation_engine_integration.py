import unittest
import uuid
import random
import io

from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    incident_auto_escalation_engine
)
from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.incident_notification_bridge import incident_notification_bridge

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.incident_id = f"INC-{uuid.uuid4()}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.trend_value = round(random.uniform(1.0, 10.0), 2)

    def test_evaluate_and_escalate_integration(self):
        payload = {
            "id": self.incident_id,
            "severity": self.severity_level,
            "trend": self.trend_value
        }

        agg_result = incident_aggregator(payload)
        self.assertIsNotNone(agg_result)

        severity_result = incident_severity_evaluator(payload)
        trend_result = incident_trend_analyzer(self.incident_id)

        escalation_decision = incident_auto_escalation_engine(severity_result, trend_result)

        self.assertTrue(escalation_decision.get("escalate"))
        self.assertEqual(escalation_decision.get("severity"), severity_result.get("severity"))

        result = self.engine.evaluate_and_escalate(payload)

        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertEqual(result.get("severity"), self.severity_level)
        self.assertEqual(result.get("trend_score"), self.trend_value)
        self.assertEqual(result.get("status"), "SUCCESS")

        notification_payload = {
            "incident_id": self.incident_id,
            "destination": escalation_decision.get("destination")
        }
        notif_result = incident_notification_bridge(notification_payload)
        self.assertIsNotNone(notif_result)

    def test_process_stream_integration(self):
        stream_data = f"METRIC:CPU,INCIDENT_ID:{self.incident_id},STATUS:ACTIVE"
        stream = io.BytesIO(stream_data.encode('utf-8'))

        stream_result = self.engine.process_stream(stream)

        self.assertTrue(stream_result.get("processed"))
        self.assertEqual(stream_result.get("stream_id"), self.incident_id)
        self.assertEqual(stream_result.get("action"), "AUTO_ESCALATE")

    def test_analyze_trends_integration(self):
        trend_analysis = self.engine.analyze_trends(self.incident_id)
        self.assertIn("trend_score", trend_analysis)
        self.assertIsInstance(trend_analysis.get("trend_score"), float)

if __name__ == "__main__":
    unittest.main()