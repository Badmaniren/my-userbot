import unittest
from unittest.mock import MagicMock
import random
import uuid
import string

from skills.incident_digest_generator import IncidentDigestGenerator

class TestIncidentDigestGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_health_aggregator = MagicMock()
        self.mock_incident_aggregator = MagicMock()
        self.mock_template_engine = MagicMock()
        self.mock_channel_dispatcher = MagicMock()

        self.generator = IncidentDigestGenerator(
            system_health_aggregator=self.mock_health_aggregator,
            incident_aggregator=self.mock_incident_aggregator,
            notification_template_engine=self.mock_template_engine,
            notification_channel_dispatcher=self.mock_channel_dispatcher
        )

    def _generate_random_string(self, length=12):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_email(self):
        return f"{self._generate_random_string()}@{self._generate_random_string()}.{random.choice(['com', 'net', 'org', 'io'])}"

    def test_generate_digest_success(self):
        stakeholder_id = f"stakeholder_{uuid.uuid4().hex}"
        timeframe_hours = random.randint(1, 168)

        health_score = round(random.uniform(10.0, 100.0), 2)
        system_status = f"STATUS_{uuid.uuid4().hex}"
        mock_health_data = {
            "average_score": health_score,
            "status": system_status,
            "metrics_evaluated": random.randint(100, 10000)
        }

        incident_id_1 = f"INC-{uuid.uuid4().hex[:8].upper()}"
        incident_id_2 = f"INC-{uuid.uuid4().hex[:8].upper()}"
        incident_desc_1 = f"Error: {self._generate_random_string(20)}"
        incident_desc_2 = f"Failure: {self._generate_random_string(20)}"

        mock_incidents = [
            {"id": incident_id_1, "description": incident_desc_1, "severity": "CRITICAL"},
            {"id": incident_id_2, "description": incident_desc_2, "severity": "WARNING"}
        ]

        self.mock_health_aggregator.get_aggregated_health.return_value = mock_health_data
        self.mock_incident_aggregator.get_incidents.return_value = mock_incidents

        digest = self.generator.generate_digest(stakeholder_id, timeframe_hours)

        self.assertEqual(digest["stakeholder_id"], stakeholder_id)
        self.assertEqual(digest["timeframe_hours"], timeframe_hours)
        self.assertEqual(digest["health_summary"]["average_score"], health_score)
        self.assertEqual(digest["health_summary"]["status"], system_status)

        self.assertEqual(len(digest["incidents"]), 2)
        self.assertEqual(digest["incidents"][0]["id"], incident_id_1)
        self.assertEqual(digest["incidents"][0]["description"], incident_desc_1)
        self.assertEqual(digest["incidents"][1]["id"], incident_id_2)
        self.assertEqual(digest["incidents"][1]["description"], incident_desc_2)

        self.mock_health_aggregator.get_aggregated_health.assert_called_once_with(timeframe_hours)
        self.mock_incident_aggregator.get_incidents.assert_called_once_with(timeframe_hours)

    def test_send_digest_success(self):
        stakeholder_email = self._generate_random_email()
        digest_id = f"digest_{uuid.uuid4().hex}"
        digest_data = {
            "digest_id": digest_id,
            "stakeholder_id": f"user_{uuid.uuid4().hex}",
            "incidents_count": random.randint(1, 50)
        }
        rendered_template = f"<html><body>{uuid.uuid4().hex}</body></html>"
        dispatch_receipt = f"receipt_{uuid.uuid4().hex}"

        self.mock_template_engine.render.return_value = rendered_template
        self.mock_channel_dispatcher.dispatch.return_value = dispatch_receipt

        result = self.generator.send_digest(stakeholder_email, digest_data)

        self.assertEqual(result, dispatch_receipt)
        self.mock_template_engine.render.assert_called_once_with(digest_data)
        self.mock_channel_dispatcher.dispatch.assert_called_once_with(stakeholder_email, rendered_template)

    def test_generate_digest_empty_data(self):
        stakeholder_id = f"stakeholder_{uuid.uuid4().hex}"
        timeframe_hours = random.randint(1, 168)

        self.mock_health_aggregator.get_aggregated_health.return_value = {}
        self.mock_incident_aggregator.get_incidents.return_value = []

        digest = self.generator.generate_digest(stakeholder_id, timeframe_hours)

        self.assertEqual(digest["stakeholder_id"], stakeholder_id)
        self.assertEqual(digest["timeframe_hours"], timeframe_hours)
        self.assertEqual(digest["health_summary"], {})
        self.assertEqual(digest["incidents"], [])

    def test_generate_digest_propagates_exception(self):
        stakeholder_id = f"stakeholder_{uuid.uuid4().hex}"
        timeframe_hours = random.randint(1, 168)
        error_message = f"Database failure: {uuid.uuid4().hex}"

        self.mock_health_aggregator.get_aggregated_health.side_effect = RuntimeError(error_message)

        with self.assertRaises(RuntimeError) as context:
            self.generator.generate_digest(stakeholder_id, timeframe_hours)

        self.assertIn(error_message, str(context.exception))

if __name__ == "__main__":
    unittest.main()