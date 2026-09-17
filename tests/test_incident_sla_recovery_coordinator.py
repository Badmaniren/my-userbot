import unittest
from unittest.mock import MagicMock, patch
import datetime
import uuid
import random
import io

from skills.incident_sla_recovery_coordinator import IncidentSLARecoveryCoordinator


class TestIncidentSLARecoveryCoordinator(unittest.TestCase):
    def setUp(self):
        self.mock_sla_tracker = MagicMock()
        self.mock_recovery_dispatcher = MagicMock()
        self.coordinator = IncidentSLARecoveryCoordinator(
            sla_tracker=self.mock_sla_tracker,
            recovery_dispatcher=self.mock_recovery_dispatcher
        )

    def test_coordinate_recovery_cycle_dispatches_successfully(self):
        inc_id = str(uuid.uuid4())
        mod_name = f"module_{uuid.uuid4().hex[:6]}"
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        breached_incident = {
            'incident_id': inc_id,
            'module_name': mod_name,
            'severity': sev
        }
        self.mock_sla_tracker.check_sla_breaches.return_value = [breached_incident]
        
        expected_dispatch_res = {'status': 'dispatched', 'id': str(uuid.uuid4())}
        self.mock_recovery_dispatcher.dispatch_recovery.return_value = expected_dispatch_res

        notif_bridge = MagicMock()
        escalation_engine = MagicMock()

        results = self.coordinator.coordinate_recovery_cycle(
            current_time, notification_bridge=notif_bridge, escalation_engine=escalation_engine
        )

        self.mock_sla_tracker.check_sla_breaches.assert_called_once_with(
            current_time, notif_bridge, escalation_engine
        )
        self.mock_recovery_dispatcher.dispatch_recovery.assert_called_once_with(
            incident_id=inc_id,
            module_name=mod_name,
            severity=sev
        )
        self.assertEqual(results, [expected_dispatch_res])

    def test_coordinate_recovery_cycle_fallback_type_error(self):
        inc_id = str(uuid.uuid4())
        mod_name = f"module_{uuid.uuid4().hex[:6]}"
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        breached_incident = {
            'incident_id': inc_id,
            'module_name': mod_name,
            'severity': sev
        }
        self.mock_sla_tracker.check_sla_breaches.return_value = [breached_incident]
        
        fallback_res = {'status': 'fallback_success', 'id': str(uuid.uuid4())}
        
        def dispatch_side_effect(*args, **kwargs):
            if 'severity' in kwargs or len(args) > 2:
                raise TypeError("Unexpected argument")
            if len(kwargs) == 2 or len(args) == 2:
                return fallback_res
            raise TypeError("Still wrong signature")

        self.mock_recovery_dispatcher.dispatch_recovery.side_effect = dispatch_side_effect

        results = self.coordinator.coordinate_recovery_cycle(current_time)

        self.assertEqual(results, [fallback_res])
        self.assertEqual(self.mock_recovery_dispatcher.dispatch_recovery.call_count, 2)

    def test_coordinate_recovery_cycle_all_dispatches_fail_returns_default(self):
        inc_id = str(uuid.uuid4())
        mod_name = f"module_{uuid.uuid4().hex[:6]}"
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        breached_incident = {
            'incident_id': inc_id,
            'module_name': mod_name,
            'severity': sev
        }
        self.mock_sla_tracker.check_sla_breaches.return_value = [breached_incident]
        
        self.mock_recovery_dispatcher.dispatch_recovery.side_effect = TypeError("Incompatible")

        results = self.coordinator.coordinate_recovery_cycle(current_time)

        expected = [{
            'status': 'recovered',
            'incident_id': inc_id
        }]
        self.assertEqual(results, expected)

    def test_register_incident_to_track(self):
        inc_id = str(uuid.uuid4())
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        
        expected_res = {"status": "registered", "incident_id": inc_id, "extra": uuid.uuid4().hex}
        self.mock_sla_tracker.register_incident.return_value = expected_res

        res = self.coordinator.register_incident_to_track(inc_id, sev, created_at)

        self.mock_sla_tracker.register_incident.assert_called_once_with(inc_id, sev, created_at)
        self.assertEqual(res, expected_res)

    def test_register_incident_to_track_default_none(self):
        inc_id = str(uuid.uuid4())
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        created_at = datetime.datetime.now(datetime.timezone.utc)
        
        self.mock_sla_tracker.register_incident.return_value = None

        res = self.coordinator.register_and_track(inc_id, sev, created_at)

        self.assertEqual(res, {"status": "tracked", "incident_id": inc_id})

    def test_handle_failure(self):
        mod_name = f"mod_{uuid.uuid4().hex[:8]}"
        exc = Exception(uuid.uuid4().hex)
        context = {"context_id": uuid.uuid4().hex}
        expected_dispatch = {"handled": True, "token": uuid.uuid4().hex}
        self.mock_recovery_dispatcher.handle_runtime_failure.return_value = expected_dispatch

        res = self.coordinator.handle_failure(mod_name, exc, context)

        self.mock_recovery_dispatcher.handle_runtime_failure.assert_called_once_with(mod_name, exc, context)
        self.assertEqual(res, expected_dispatch)

    def test_process_incoming_stream(self):
        expected_stream_res = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_recovery_dispatcher.consume_and_process_stream.return_value = expected_stream_res

        res = self.coordinator.process_incoming_stream()

        self.mock_recovery_dispatcher.consume_and_process_stream.assert_called_once()
        self.assertEqual(res, expected_stream_res)

    def test_get_current_time_to_breach_timestamp(self):
        inc_id = str(uuid.uuid4())
        ts = random.randint(1600000000, 1800000000)
        expected_time = random.uniform(10.0, 500.0)
        
        self.mock_sla_tracker.incidents = {
            inc_id: {'created_at': ts - 100}
        }
        self.mock_sla_tracker.get_time_to_breach.return_value = expected_time

        res = self.coordinator.get_current_time_to_breach(inc_id, ts)

        self.assertEqual(res, expected_time)
        self.assertEqual(self.mock_sla_tracker.incidents[inc_id]['created_at'].tzinfo, datetime.timezone.utc)

    def test_get_current_time_to_breach_datetime(self):
        inc_id = str(uuid.uuid4())
        dt = datetime.datetime.now(datetime.timezone.utc)
        expected_time = random.uniform(1.0, 50.0)
        
        self.mock_sla_tracker.incidents = {
            inc_id: {'created_at': datetime.datetime.now()}
        }
        self.mock_sla_tracker.get_time_to_breach.return_value = expected_time

        res = self.coordinator.get_current_time_to_breach(inc_id, dt)

        self.assertEqual(res, expected_time)
        self.assertEqual(self.mock_sla_tracker.incidents[inc_id]['created_at'].tzinfo, datetime.timezone.utc)

    def test_get_current_time_to_breach_no_attr(self):
        inc_id = str(uuid.uuid4())
        dt = datetime.datetime.now(datetime.timezone.utc)
        
        del self.mock_sla_tracker.get_time_to_breach
        res = self.coordinator.get_current_time_to_breach(inc_id, dt)
        self.assertEqual(res, 0.0)

    def test_coordinate_recovery_for_incident(self):
        inc_id = str(uuid.uuid4())
        mod_name = f"mod_{uuid.uuid4().hex[:5]}"
        exc = RuntimeError(uuid.uuid4().hex)
        dispatch_res = {"success": True, "details": uuid.uuid4().hex}
        
        self.mock_recovery_dispatcher.handle_runtime_failure.return_value = dispatch_res

        res = self.coordinator.coordinate_recovery_for_incident(inc_id, mod_name, exc)

        self.mock_recovery_dispatcher.handle_runtime_failure.assert_called_once_with(
            mod_name, exc, {"incident_id": inc_id}
        )
        self.assertEqual(res, {
            "dispatch_result": dispatch_res,
            "incident_id": inc_id
        })

    def test_evaluate_coordinator_telemetry(self):
        telemetry_data = {"metric": uuid.uuid4().hex, "value": random.randint(1, 100)}
        self.mock_sla_tracker.get_telemetry.return_value = telemetry_data

        res = self.coordinator.evaluate_coordinator_telemetry()

        self.assertEqual(res, telemetry_data)

    def test_evaluate_coordinator_telemetry_missing(self):
        del self.mock_sla_tracker.get_telemetry
        res = self.coordinator.evaluate_coordinator_telemetry()
        self.assertEqual(res, {})


if __name__ == '__main__':
    unittest.main()