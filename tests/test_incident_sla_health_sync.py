import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.incident_sla_health_sync import (
    sync_sla_with_health,
    process_sla_stream,
    validate_and_sync,
    sync_sla_to_health_aggregator
)

class TestIncidentSLAHealthSync(unittest.TestCase):

    def test_sync_sla_with_health_logic(self):
        random_token = uuid.uuid4().hex
        random_health = random.uniform(0.0, 100.0)
        sla_data = {"token": random_token}

        mock_aggregator = MagicMock(return_value=random_health)

        result = sync_sla_with_health(sla_data, mock_aggregator)

        self.assertEqual(result["status"], "synchronized")
        self.assertEqual(result["token"], random_token)
        self.assertEqual(result["health_score"], random_health)
        mock_aggregator.assert_called_once()

    def test_process_sla_stream_integrity(self):
        random_content = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_content)

        result = process_sla_stream(stream)

        self.assertEqual(result, len(random_content))

    def test_validate_and_sync_payload(self):
        random_id = uuid.uuid4().hex
        valid_payload = {"id": random_id, "meta": random.random()}

        self.assertTrue(validate_and_sync(valid_payload))

        with self.assertRaises(TypeError):
            validate_and_sync({"wrong_key": random_id})

    def test_sync_sla_to_health_aggregator_integration(self):
        random_incident_id = uuid.uuid4().hex
        random_status = uuid.uuid4().hex
        random_impact = random.randint(1, 10)

        test_payload = {
            "incident_id": random_incident_id,
            "sla_status": random_status,
            "impact_score": random_impact
        }

        with patch('skills.incident_sla_health_sync.IncidentSLATracker') as MockTracker:
            with patch('skills.incident_sla_health_sync.SystemHealthAggregator') as MockAggregator:
                instance_tracker = MockTracker.return_value
                instance_aggregator = MockAggregator.return_value

                result = sync_sla_to_health_aggregator(test_payload)

                self.assertEqual(result["incident_id"], random_incident_id)
                self.assertTrue(result["success"])

                instance_tracker.save_incident_data.assert_called_with(
                    random_incident_id, {"status": random_status}
                )
                instance_aggregator.update_system_health.assert_called_with(
                    random_incident_id, {"impact_score": random_impact}
                )

if __name__ == '__main__':
    unittest.main()