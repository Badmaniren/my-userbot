import unittest
import uuid
import random
import time

from skills.incident_severity_classifier import IncidentSeverityClassifier
from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.error_recovery_hub import ErrorRecoveryHub

class TestIncidentSeverityClassifierIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = IncidentAggregator()
        self.trend_analyzer = IncidentTrendAnalyzer(incident_aggregator=self.aggregator)
        self.classifier = IncidentSeverityClassifier(
            incident_aggregator=self.aggregator,
            incident_trend_analyzer=self.trend_analyzer
        )
        self.recovery_hub = ErrorRecoveryHub(
            incident_severity_classifier=self.classifier
        )

    def test_integration_flow_critical_incident(self):
        incident_id = str(uuid.uuid4())
        critical_component = "payment_gateway"
        random_error_code = f"ERR_{random.randint(500, 599)}"

        frequency_count = random.randint(15, 30)
        for _ in range(frequency_count):
            temp_id = str(uuid.uuid4())
            self.aggregator.register_incident(
                incident_id=temp_id,
                component=critical_component,
                metadata={"error_code": random_error_code, "timestamp": time.time()}
            )

        self.aggregator.register_incident(
            incident_id=incident_id,
            component=critical_component,
            metadata={"error_code": random_error_code, "timestamp": time.time()}
        )

        classification_result = self.classifier.classify_incident(incident_id)

        self.assertEqual(classification_result["incident_id"], incident_id)
        self.assertEqual(classification_result["severity"], "critical")
        self.assertTrue(classification_result["frequency_count"] >= frequency_count + 1)

        recovery_action = self.recovery_hub.process_incident(incident_id)
        self.assertEqual(recovery_action["incident_id"], incident_id)
        self.assertEqual(recovery_action["strategy"], "immediate_failover")
        self.assertTrue(recovery_action["executed"])

    def test_integration_flow_low_severity_incident(self):
        incident_id = str(uuid.uuid4())
        non_critical_component = random.choice(["frontend_ui", "documentation_server"])
        random_error_code = f"WARN_{random.randint(100, 199)}"

        self.aggregator.register_incident(
            incident_id=incident_id,
            component=non_critical_component,
            metadata={"error_code": random_error_code, "timestamp": time.time()}
        )

        classification_result = self.classifier.classify_incident(incident_id)

        self.assertEqual(classification_result["incident_id"], incident_id)
        self.assertEqual(classification_result["severity"], "low")
        self.assertEqual(classification_result["frequency_count"], 1)

        recovery_action = self.recovery_hub.process_incident(incident_id)
        self.assertEqual(recovery_action["incident_id"], incident_id)
        self.assertEqual(recovery_action["strategy"], "log_and_ignore")
        self.assertTrue(recovery_action["executed"])

if __name__ == "__main__":
    unittest.main()