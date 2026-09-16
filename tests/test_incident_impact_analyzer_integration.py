import unittest
import uuid
import random
import os
import tempfile
from skills.incident_impact_analyzer import IncidentImpactAnalyzer
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub

class TestIncidentImpactAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = IncidentImpactAnalyzer()
        self.aggregator = IncidentAggregator()
        self.recovery_hub = ErrorRecoveryHub()
        self.test_incident_id = str(uuid.uuid4())
        self.test_metric_value = random.uniform(100.0, 10000.0)
        self.test_downtime_minutes = random.randint(5, 120)

    def test_analyze_incident_impact_end_to_end(self):
        incident_data = {
            "incident_id": self.test_incident_id,
            "error_rate": self.test_metric_value,
            "downtime_minutes": self.test_downtime_minutes,
            "affected_services": ["auth-service", "payment-gateway"],
            "severity": "CRITICAL"
        }
        
        aggregated_incident = self.aggregator.aggregate(incident_data)
        self.assertEqual(aggregated_incident.get("incident_id"), self.test_incident_id)

        recovery_logs = self.recovery_hub.process_recovery({
            "incident_id": self.test_incident_id,
            "status": "RECOVERED",
            "recovery_time_seconds": random.randint(30, 300)
        })
        self.assertIsNotNone(recovery_logs)

        impact_report = self.analyzer.analyze({
            "incident": aggregated_incident,
            "recovery_logs": recovery_logs
        })

        self.assertIn("financial_loss", impact_report)
        self.assertIn("operational_impact_score", impact_report)
        self.assertEqual(impact_report["incident_id"], self.test_incident_id)
        self.assertGreater(impact_report["financial_loss"], 0.0)

if __name__ == "__main__":
    unittest.main()