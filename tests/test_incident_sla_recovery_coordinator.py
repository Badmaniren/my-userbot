import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import datetime

from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator


class TestIncidentSLARecoveryCoordinator(unittest.TestCase):

    def setUp(self):
        self.sla_thresholds = {
            random.choice(['P1', 'P2', 'P3']): random.randint(30, 3600)
            for _ in range(3)
        }
        self.warning_threshold_pct = random.uniform(0.5, 0.9)
        self.coordinator = IncidentSLARecoveryCoordinator(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

    def test_init_composition_success(self):
        self.assertIsNotNone(self.coordinator.sla_tracker)
        self.assertIsNotNone(self.coordinator.recovery_dispatcher)

    @patch('skills.incident_sla_recovery_coordinator.IncidentSLATracker')
    @patch('skills.incident_sla_recovery_coordinator.IncidentAutoRecoveryDispatcher')
    def test_coordinate_recovery_cycle_breached(self, mock_dispatcher_cls, mock_tracker_cls):
        mock_tracker_instance = mock_tracker_cls.return_value
        mock_dispatcher_instance = mock_dispatcher_cls.return_value

        incident_id = uuid.uuid4().hex
        module_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity = random.choice(['CRITICAL', 'HIGH', 'MEDIUM'])
        current_time = datetime.datetime.now().timestamp()
        
        breached_incident = {
            'incident_id': incident_id,
            'module_name': module_name,
            'severity': severity
        }
        mock_tracker_instance.check_sla_breaches.return_value = [breached_incident]

        mock_exception = RuntimeError(''.join(random.choices(string.ascii_letters, k=15)))
        mock_dispatcher_instance.dispatch_recovery.return_value = {
            'status': 'recovered',
            'incident_id': incident_id
        }

        coordinator = IncidentSLARecoveryCoordinator(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct
        )

        notification_bridge = MagicMock()
        escalation_engine = MagicMock()

        results = coordinator.coordinate_recovery_cycle(
            current_time=current_time,
            notification_bridge=notification_bridge,
            escalation_engine=escalation_engine
        )

        mock_tracker_instance.check_sla_breaches.assert_called_once_with(
            current_time, notification_bridge, escalation_engine
        )
        mock_dispatcher_instance.dispatch_recovery.assert_called_once()
        self.assertIn(incident_id, [res.get('incident_id') for res in results])

    def test_register_and_track_incident(self):
        incident_id = uuid.uuid4().hex
        severity = random.choice(['P1', 'P2', 'P3'])
        created_at = datetime.datetime.now().timestamp()

        with patch.object(self.coordinator.sla_tracker, 'register_incident') as mock_register:
            self.coordinator.register_incident_to_track(incident_id, severity, created_at)
            mock_register.assert_called_once_with(incident_id, severity, created_at)

    def test_handle_runtime_failure_delegation(self):
        module_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        error_msg = ''.join(random.choices(string.ascii_letters, k=20))
        exception = ValueError(error_msg)
        context = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.coordinator.recovery_dispatcher, 'handle_runtime_failure') as mock_handle:
            self.coordinator.handle_failure(module_name, exception, context)
            mock_handle.assert_called_once_with(module_name, exception, context)

    def test_stream_processing_pipeline(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        
        with patch.object(self.coordinator.recovery_dispatcher, 'consume_and_process_stream', return_value=random_bytes.getvalue()) as mock_stream:
            result = self.coordinator.process_incoming_stream()
            mock_stream.assert_called_once()
            self.assertEqual(result, random_bytes.getvalue())


if __name__ == '__main__':
    unittest.main()