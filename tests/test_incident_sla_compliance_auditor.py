import unittest
from unittest.mock import patch, MagicMock
import json
import io
import uuid
import random
from skills.incident_sla_compliance_auditor import (
    IncidentSlaComplianceAuditor,
    IncidentSLAComplianceAuditor,
    incident_sla_compliance_auditor
)

class TestIncidentSlaComplianceAuditor(unittest.TestCase):

    def test_generate_compliance_report(self):
        client_id = uuid.uuid4().hex
        total = random.randint(10, 100)
        breached = random.randint(0, total)
        recovery_times = [random.randint(10, 120) for _ in range(5)]

        mock_data = {
            "client_id": client_id,
            "total_incidents": total,
            "breached_incidents": breached,
            "recovery_times_minutes": recovery_times
        }

        file_content = json.dumps(mock_data)
        random_filepath = f"{uuid.uuid4().hex}.json"

        expected_compliance = round(((total - breached) / total) * 100, 2) if total > 0 else 100.0
        expected_gaps = [t for t in recovery_times if t > 60]

        auditor = IncidentSlaComplianceAuditor()

        with patch("builtins.open", return_value=io.StringIO(file_content)) as mock_file:
            result = auditor.generate_compliance_report(random_filepath)
            mock_file.assert_called_once_with(random_filepath, 'r')

        self.assertEqual(result.get("client_id"), client_id)
        self.assertEqual(result.get("compliance_percentage"), expected_compliance)
        self.assertEqual(result.get("systemic_gaps_identified"), expected_gaps)

    def test_audit_compliance_dict_and_class_alias(self):
        auditor = IncidentSLAComplianceAuditor()
        data = {
            "client_id": "client_abc",
            "total_incidents": 10,
            "breached_incidents": 2,
            "recovery_times_minutes": [30, 45, 90, 15]
        }
        result = auditor.audit_compliance(data)
        self.assertEqual(result.get("client_id"), "client_abc")
        self.assertEqual(result.get("compliance_percentage"), 80.0)
        self.assertEqual(result.get("systemic_gaps_identified"), [90])

    def test_identify_systemic_gaps(self):
        id_1 = uuid.uuid4().hex
        id_2 = uuid.uuid4().hex
        duration_1 = random.randint(1, 120)
        duration_2 = random.randint(121, 300)

        mock_data = {
            "incidents": [
                {"id": id_1, "duration": duration_1},
                {"id": id_2, "duration": duration_2}
            ]
        }

        file_content = json.dumps(mock_data)
        random_filepath = f"{uuid.uuid4().hex}.json"

        auditor = IncidentSlaComplianceAuditor()

        with patch("builtins.open", return_value=io.StringIO(file_content)) as mock_file:
            gaps = auditor.identify_systemic_gaps(random_filepath)
            mock_file.assert_called_once_with(random_filepath, 'r')

        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0].get("id"), id_2)
        self.assertEqual(gaps[0].get("duration"), duration_2)

    def test_audit_recovery_performance_from_api(self):
        endpoint = f"https://api.{uuid.uuid4().hex}.internal/audit"
        token = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        api_response_data = {"incident_id": incident_id, "status": "reviewed"}

        mock_response = MagicMock()
        mock_response.json.return_value = api_response_data

        auditor = IncidentSlaComplianceAuditor()

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = auditor.audit_recovery_performance_from_api(endpoint, token)
            mock_get.assert_called_once_with(
                endpoint,
                headers={"Authorization": f"Bearer {token}"}
            )

        self.assertEqual(result.get("audited_incidents"), api_response_data)


class TestIncidentSlaComplianceAuditorIntegration(unittest.TestCase):

    def test_incident_sla_compliance_auditor_compliant(self):
        incident_id = uuid.uuid4().hex
        target = random.randint(30, 60)
        res_time = target - random.randint(1, 10)

        tracked_sla = {
            "incident_id": incident_id,
            "resolution_time_minutes": res_time,
            "sla_target_minutes": target
        }

        result = incident_sla_compliance_auditor(tracked_sla)

        self.assertEqual(result.get("audited_incident_id"), incident_id)
        self.assertEqual(result.get("compliance_status"), "COMPLIANT")

    def test_incident_sla_compliance_auditor_breach(self):
        incident_id = uuid.uuid4().hex
        target = random.randint(30, 60)
        res_time = target + random.randint(1, 30)

        tracked_sla = {
            "incident_id": incident_id,
            "resolution_time_minutes": res_time,
            "sla_target_minutes": target
        }

        result = incident_sla_compliance_auditor(tracked_sla)

        self.assertEqual(result.get("audited_incident_id"), incident_id)
        self.assertEqual(result.get("compliance_status"), "BREACH")

if __name__ == "__main__":
    unittest.main()
