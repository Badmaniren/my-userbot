import unittest
import uuid
import io
from skills import incident_forensic_integrator

class TestIncidentForensicIntegratorIntegration(unittest.TestCase):
    def test_start_new_integration_flow(self):
        random_incident_id = f"INC-{uuid.uuid4()}"
        random_telemetry_data = f"telemetry_metric_{uuid.uuid4()}".encode("utf-8")
        telemetry_source = io.BytesIO(random_telemetry_data)

        result = incident_forensic_integrator.start_new(
            incident_id=random_incident_id,
            telemetry_source=telemetry_source,
            deep_inspection=True
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], random_incident_id)
        self.assertIn("severity", result)

    def test_start_new_with_uuid_and_no_source(self):
        random_uuid = str(uuid.uuid4())

        result = incident_forensic_integrator.start_new(
            incident_uuid=random_uuid,
            deep_inspection=False
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), random_uuid)

    def test_start_new_invalid_identifier_raises_value_error(self):
        with self.assertRaises(ValueError):
            incident_forensic_integrator.start_new(
                incident_id="",
                deep_inspection=False
            )

if __name__ == "__main__":
    unittest.main()