import unittest
from unittest.mock import MagicMock, patch, mock_open
import io
import uuid
import random
import json

from skills.incident_recovery_duration_tracker import IncidentRecoveryDurationTracker, track_recovery_duration

class TestIncidentRecoveryDurationTracker(unittest.TestCase):
    def setUp(self):
        self.mock_aggregator = MagicMock()
        self.tracker = IncidentRecoveryDurationTracker(self.mock_aggregator)

    def test_calculate_recovery_duration_success(self):
        incident_id = uuid.uuid4().hex
        start = random.randint(1000, 5000)
        end = start + random.randint(100, 1000)
        expected_duration = end - start

        self.mock_aggregator.get_incident_data.return_value = {
            "start_timestamp": start,
            "end_timestamp": end
        }

        result = self.tracker.calculate_recovery_duration(incident_id)
        self.assertEqual(result, expected_duration)
        self.mock_aggregator.get_incident_data.assert_called_once_with(incident_id)

    def test_calculate_recovery_duration_not_found(self):
        incident_id = uuid.uuid4().hex
        self.mock_aggregator.get_incident_data.return_value = None

        with self.assertRaises(ValueError):
            self.tracker.calculate_recovery_duration(incident_id)

    def test_track_downtime_logic(self):
        incident_id = uuid.uuid4().hex
        random_duration = random.uniform(10.0, 500.0)

        with patch.object(self.tracker, '_fetch_raw_logs') as mock_logs:
            mock_logs.return_value = io.BytesIO(uuid.uuid4().bytes)
            self.mock_aggregator.get_downtime_metrics.return_value = {"duration": random_duration}

            result = self.tracker.track_downtime(incident_id)
            self.assertEqual(result, random_duration)
            mock_logs.assert_called_once_with(incident_id)

    def test_generate_recovery_report_structure(self):
        incident_id = uuid.uuid4().hex
        duration = random.random() * 100

        with patch.object(self.tracker, 'calculate_recovery_duration', return_value=duration):
            report = self.tracker.generate_recovery_report(incident_id)
            self.assertEqual(report["incident_id"], incident_id)
            self.assertEqual(report["duration"], float(duration))

class TestFunctionalRecoveryTracker(unittest.TestCase):
    def test_track_recovery_duration_integration(self):
        incident_id = uuid.uuid4().hex
        start = random.randint(1, 100)
        end = start + random.randint(1, 100)
        duration = end - start

        mock_data = {"start_timestamp": start, "end_timestamp": end}

        with patch('skills.incident_recovery_duration_tracker.get_incident_data', return_value=mock_data) as mock_get:
            with patch('skills.incident_recovery_duration_tracker.store_incident_metrics') as mock_store:
                with patch("builtins.open", mock_open()) as mocked_file:
                    result = track_recovery_duration(incident_id)

                    self.assertEqual(result["incident_id"], incident_id)
                    self.assertEqual(result["duration_seconds"], duration)
                    mock_store.assert_called_once()
                    mocked_file.assert_called_once()

                    # Проверка записи JSON
                    args, _ = mocked_file.call_args
                    self.assertIn(incident_id, args[0])

    def test_track_recovery_duration_none_case(self):
        incident_id = uuid.uuid4().hex
        with patch('skills.incident_recovery_duration_tracker.get_incident_data', return_value=None):
            result = track_recovery_duration(incident_id)
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
