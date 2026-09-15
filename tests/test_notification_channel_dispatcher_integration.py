import unittest
import uuid
import random
import os
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator

class TestNotificationChannelDispatcherIntegration(unittest.TestCase):
    def test_notification_dispatch_flow(self):
        random_suffix = uuid.uuid4().hex[:8]
        module_name = f"test_module_{random_suffix}"
        exception_msg = f"Critical failure in subsystem {random_suffix}"
        test_exception = RuntimeError(exception_msg)
        traceback_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line {random.randint(1, 100)}\n    raise RuntimeError('{exception_msg}')"
        
        hub = ErrorRecoveryHub()
        incident_id = f"inc-{uuid.uuid4()}"
        
        capture_res = hub.capture_failure(module_name, test_exception, traceback_str)
        self.assertIsNotNone(capture_res)
        
        aggregator = IncidentAggregator()
        aggregated_data = aggregator.process_and_aggregate(module_name, test_exception, traceback_str, incident_id)
        self.assertIsNotNone(aggregated_data)
        
        dispatcher = NotificationChannelDispatcher()
        
        dispatch_methods = [m for m in dir(dispatcher) if callable(getattr(dispatcher, m)) and not m.startswith("_")]
        self.assertTrue(len(dispatch_methods) > 0, "Dispatcher must have operational methods")
        
        method_name = dispatch_methods[0]
        dispatch_method = getattr(dispatcher, method_name)
        
        try:
            result = dispatch_method(incident_id, aggregated_data)
        except TypeError:
            try:
                result = dispatch_method(aggregated_data)
            except TypeError:
                result = dispatch_method(incident_id)
                
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()