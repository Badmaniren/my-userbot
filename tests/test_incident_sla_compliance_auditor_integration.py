import unittest
import json
import os
import uuid
import random
from skills.incident_sla_compliance_auditor import IncidentSlaComplianceAuditor, incident_sla_compliance_auditor
try:
    from skills.incident_sla_tracker import incident_sla_tracker
except ImportError:
    from skills.incident_sla_tracker import track_incident_sla as incident_sla_tracker

class TestIncidentSlaComplianceAuditorIntegration(unittest.TestCase):

    def setUp(self):
        self.auditor = IncidentSlaComplianceAuditor()
        self.test_file = f"test_data_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_full_compliance_audit_flow(self):
        # 1. Generate random incident data
        client_id = str(uuid.uuid4())
        total = random.randint(10, 50)
        breached = random.randint(0, 5)
        recovery_times = [random.randint(10, 120) for _ in range(total)]

        data = {
            "client_id": client_id,
            "total_incidents": total,
            "breached_incidents": breached,
            "recovery_times_minutes": recovery_times
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        # 2. Execute Auditor logic
        report = self.auditor.generate_compliance_report(self.test_file)

        # 3. Verify integration results
        self.assertEqual(report["client_id"], client_id)
        self.assertIn("compliance_percentage", report)
        self.assertIsInstance(report["systemic_gaps_identified"], list)

        # Verify calculation logic
        expected_pct = round(((total - breached) / total) * 100, 2)
        self.assertEqual(report["compliance_percentage"], expected_pct)

    def test_sla_tracker_to_auditor_integration(self):
        # Integration between incident_sla_tracker and incident_sla_compliance_auditor
        incident_id = str(uuid.uuid4())
        res_time = random.randint(30, 150)
        target = 60

        # Simulate tracking via incident_sla_tracker
        tracked_data = {
            "incident_id": incident_id,
            "resolution_time_minutes": res_time,
            "sla_target_minutes": target
        }

        # Process through integration helper
        result = incident_sla_compliance_auditor(tracked_data)

        # Verify status logic
        expected_status = "COMPLIANT" if res_time <= target else "BREACH"

        self.assertEqual(result["audited_incident_id"], incident_id)
        self.assertEqual(result["compliance_status"], expected_status)

    def test_systemic_gaps_identification(self):
        # Test logic for identifying gaps > 120 mins
        incident_id_1 = str(uuid.uuid4())
        incident_id_2 = str(uuid.uuid4())

        data = {
            "incidents": [
                {"id": incident_id_1, "duration": 150},
                {"id": incident_id_2, "duration": 30}
            ]
        }

        with open(self.test_file, 'w') as f:
            json.dump(data, f)

        gaps = self.auditor.identify_systemic_gaps(self.test_file)

        # Verify that only the incident > 120 is caught
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["id"], incident_id_1)
        self.assertGreater(gaps[0]["duration"], 120)

if __name__ == '__main__':
    unittest.main()
