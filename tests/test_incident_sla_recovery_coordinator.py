import datetime
import random
import uuid
import unittest
from unittest.mock import MagicMock, patch

from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator


class TestIncidentSLARecoveryCoordinator(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.sla_thresholds = {
            random.choice(['P1', 'P2', 'P3']): random.randint(100, 3600)
        }
        self.warning_threshold_pct = random.uniform(0.5, 0.9)
        
        self.mock_sla_tracker = MagicMock()
        self.mock_recovery_dispatcher = MagicMock()
        
        self.coordinator = IncidentSLARecoveryCoordinator(
            sla_thresholds=self.sla_thresholds,
            warning_threshold_pct=self.warning_threshold_pct,
            sla_tracker=self.mock_sla_tracker,
            recovery_dispatcher=self.mock_recovery_dispatcher
        )

    def test_init_creates_default_dependencies(self):
        with patch('skills.incident_sla_recovery_coordinator.IncidentSLATracker') as mock_tracker_cls, \
             patch('skills.incident_sla_recovery_coordinator.IncidentAutoRecoveryDispatcher') as mock_dispatcher_cls:
            
            coord = IncidentSLARecoveryCoordinator(
                sla_thresholds=self.sla_thresholds,
                warning_threshold_pct=self.warning_threshold_pct
            )
            
            mock_tracker_cls.assert_called_once_with(
                sla_thresholds=self.sla_thresholds,
                warning_threshold_pct=self.warning_threshold_pct
            )
            mock_dispatcher_cls.assert_called_once()
            self.assertIsNotNone(coord.sla_tracker)
            self.assertIsNotNone(coord.recovery_dispatcher)

    def test_coordinate_recovery_cycle_with_dispatches(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        module_name = f"mod_{uuid.uuid4().hex}"
        severity = random.choice(['P1', 'P2', 'P3', 'P4'])
        
        breached_incident = {
            'incident_id': incident_id,
            'module_name': module_name,
            'severity': severity
        }
        self.mock_sla_tracker.check_sla_breaches.return_value = [breached_incident]
        
        expected_dispatch_res = {
            'status': f"dispatched_{uuid.uuid4().hex[:4]}",
            'incident_id': incident_id
        }
        self.mock_recovery_dispatcher.dispatch_recovery.return_value = expected_dispatch_res
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        mock_bridge = MagicMock()
        mock_escalation = MagicMock()
        
        results = self.coordinator.coordinate_recovery_cycle(
            current_time=current_time,
            notification_bridge=mock_bridge,
            escalation_engine=mock_escalation
        )
        
        self.mock_sla_tracker.check_sla_breaches.assert_called_once_with(
            current_time, mock_bridge, mock_escalation
        )
        self.mock_recovery_dispatcher.dispatch_recovery.assert_called_once_with(
            incident_id=incident_id,
            module_name=module_name,
            severity=severity
        )
        self.assertEqual(results, [expected_dispatch_res])

    def test_coordinate_recovery_cycle_fallback_to_default_recovered(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        module_name = f"mod_{uuid.uuid4().hex}"
        severity = random.choice(['P1', 'P2'])
        
        breached_incident = {
            'incident_id': incident_id,
            'module_name': module_name,
            'severity': severity
        }
        self.mock_sla_tracker.check_sla_breaches.return_value = [breached_incident]
        self.mock_recovery_dispatcher.dispatch_recovery.return_value = None
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        results = self.coordinator.coordinate_recovery_cycle(current_time=current_time)
        
        expected_result = {
            'status': 'recovered',
            'incident_id': incident_id
        }
        self.assertEqual(results, [expected_result])

    def test_register_incident_to_track(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        severity = random.choice(['CRITICAL', 'MAJOR', 'MINOR'])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        
        expected_return = {f"registered_{uuid.uuid4().hex}": True}
        self.mock_sla_tracker.register_incident.return_value = expected_return
        
        res = self.coordinator.register_incident_to_track(incident_id, severity, created_at)
        
        self.mock_sla_tracker.register_incident.assert_called_once_with(incident_id, severity, created_at)
        self.assertEqual(res, expected_return)

    def test_register_and_track_with_attribute(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        severity = random.choice(['HIGH', 'LOW'])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        
        expected_return = {f"status_{uuid.uuid4().hex}": "tracked"}
        self.mock_sla_tracker.register_incident = MagicMock(return_value=expected_return)
        
        res = self.coordinator.register_and_track(incident_id, severity, created_at)
        
        self.mock_sla_tracker.register_incident.assert_called_once_with(incident_id, severity, created_at)
        self.assertEqual(res, expected_return)

    def test_register_and_track_without_attribute(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        severity = random.choice(['HIGH', 'LOW'])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        
        del self.mock_sla_tracker.register_incident
        
        res = self.coordinator.register_and_track(incident_id, severity, created_at)
        self.assertIsNone(res)

    def test_handle_failure(self):
        module_name = f"mod_{uuid.uuid4().hex}"
        exception = RuntimeError(f"err_{uuid.uuid4().hex}")
        context = {f"ctx_key_{uuid.uuid4().hex}": random.randint(1, 100)}
        
        expected_res = {f"handled_{uuid.uuid4().hex}": True}
        self.mock_recovery_dispatcher.handle_runtime_failure.return_value = expected_res
        
        res = self.coordinator.handle_failure(module_name, exception, context)
        
        self.mock_recovery_dispatcher.handle_runtime_failure.assert_called_once_with(
            module_name, exception, context
        )
        self.assertEqual(res, expected_res)

    def test_process_incoming_stream(self):
        expected_res = [f"stream_item_{uuid.uuid4().hex}", random.randint(1, 50)]
        self.mock_recovery_dispatcher.consume_and_process_stream.return_value = expected_res
        
        res = self.coordinator.process_incoming_stream()
        
        self.mock_recovery_dispatcher.consume_and_process_stream.assert_called_once()
        self.assertEqual(res, expected_res)

    def test_get_current_time_to_breach_no_attribute(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        del self.mock_sla_tracker.get_time_to_breach
        
        res = self.coordinator.get_current_time_to_breach(incident_id, current_time)
        self.assertEqual(res, 0.0)

    def test_get_current_time_to_breach_with_timestamp_and_dict_conversion(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        timestamp = 1600000000.0
        current_time = timestamp + random.randint(10, 100)
        
        created_at_ts = timestamp - random.randint(10, 50)
        self.mock_sla_tracker.incidents = {
            incident_id: {'created_at': created_at_ts}
        }
        
        expected_ttb = random.uniform(1.0, 50.0)
        self.mock_sla_tracker.get_time_to_breach.return_value = expected_ttb
        
        res = self.coordinator.get_current_time_to_breach(incident_id, current_time)
        
        self.mock_sla_tracker.get_time_to_breach.assert_called_once()
        called_args = self.mock_sla_tracker.get_time_to_breach.call_args[0]
        self.assertEqual(called_args[0], incident_id)
        self.assertIsInstance(called_args[1], datetime.datetime)
        self.assertEqual(res, expected_ttb)

    def test_get_current_time_to_breach_with_naive_datetime(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        naive_dt = datetime.datetime.now()
        current_time = naive_dt + datetime.timedelta(seconds=random.randint(5, 50))
        
        self.mock_sla_tracker.incidents = {
            incident_id: {'created_at': naive_dt}
        }
        
        expected_ttb = random.uniform(5.0, 25.0)
        self.mock_sla_tracker.get_time_to_breach.return_value = expected_ttb
        
        res = self.coordinator.get_current_time_to_breach(incident_id, current_time)
        
        self.assertEqual(
            self.mock_sla_tracker.incidents[incident_id]['created_at'].tzinfo,
            datetime.timezone.utc
        )
        self.assertEqual(res, expected_ttb)

    def test_coordinate_recovery_for_incident(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        module_name = f"mod_{uuid.uuid4().hex}"
        exception = ValueError(f"val_err_{uuid.uuid4().hex}")
        
        dispatch_res = {f"dispatch_key_{uuid.uuid4().hex}": random.randint(100, 999)}
        self.mock_recovery_dispatcher.handle_runtime_failure.return_value = dispatch_res
        
        res = self.coordinator.coordinate_recovery_for_incident(incident_id, module_name, exception)
        
        self.mock_recovery_dispatcher.handle_runtime_failure.assert_called_once_with(
            module_name, exception, {"incident_id": incident_id}
        )
        self.assertEqual(res, {
            "dispatch_result": dispatch_res,
            "incident_id": incident_id
        })

    def test_coordinate_recovery_for_incident_none_dispatch(self):
        incident_id = f"inc_{uuid.uuid4().hex}"
        module_name = f"mod_{uuid.uuid4().hex}"
        exception = TypeError(f"type_err_{uuid.uuid4().hex}")
        
        self.mock_recovery_dispatcher.handle_runtime_failure.return_value = None
        
        res = self.coordinator.coordinate_recovery_for_incident(incident_id, module_name, exception)
        
        self.assertEqual(res, {
            "dispatch_result": {},
            "incident_id": incident_id
        })

    def test_evaluate_coordinator_telemetry_with_method(self):
        telemetry_data = {f"metric_{uuid.uuid4().hex}": random.random()}
        self.mock_sla_tracker.get_telemetry.return_value = telemetry_data
        
        res = self.coordinator.evaluate_coordinator_telemetry()
        
        self.mock_sla_tracker.get_telemetry.assert_called_once()
        self.assertEqual(res, telemetry_data)

    def test_evaluate_coordinator_telemetry_without_method(self):
        del self.mock_sla_tracker.get_telemetry
        
        res = self.coordinator.evaluate_coordinator_telemetry()
        self.assertEqual(res, {})


if __name__ == '__main__':
    unittest.main()