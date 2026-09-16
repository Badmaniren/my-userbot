import unittest
import uuid
import random
import os
from skills.incident_sla_compliance_auditor import incident_sla_compliance_auditor
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_aggregator import incident_aggregator

class TestIncidentSlaComplianceAuditorIntegration(unittest.TestCase):
    def test_sla_compliance_audit_pipeline(self):
        random_seed_str = str(uuid.uuid4())
        incident_id = f"inc-{random.randint(10000, 99999)}-{random_seed_str[:8]}"
        metric_value = round(random.uniform(10.5, 99.9), 2)

        aggregated_data = incident_aggregator(incident_id=incident_id, telemetry_weight=metric_value)
        self.assertIsNotNone(aggregated_data)

        tracking_result = incident_sla_tracker(incident_data=aggregated_data, threshold=metric_value)
        self.assertIsNotNone(tracking_result)

        audit_report = incident_sla_compliance_auditor(audit_target=incident_id, tracking_payload=tracking_result)

        self.assertIsInstance(audit_report, dict)
        self.assertIn("compliance_status", audit_report)
        self.assertTrue(
            any(str(incident_id) in str(val) for val in audit_report.values()),
            "Auditor must reference the generated incident ID in its compliance output."
        )

if __name__ == "__main__":
    unittest.main()