import unittest
import uuid
import random
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_metric_collector import start_new

class TestIncidentAggregatorIntegration(unittest.TestCase):
    def test_aggregate_real_incident_metrics(self):
        aggregator = IncidentAggregator()
        hub = ErrorRecoveryHub()

        module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        random_error_msg = f"Random connection failure {uuid.uuid4()}"
        exc = RuntimeError(random_error_msg)
        tb_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\nRuntimeError"

        incident_id = hub.capture_failure(module_name, exc, tb_str)
        self.assertIsNotNone(incident_id)

        analysis = hub.analyze_failure(incident_id)
        patch = hub.generate_patch(incident_id)

        success_flag = random.choice([True, False])
        metric_result = start_new(
            success=success_flag,
            incident_id=incident_id,
            error=None if success_flag else random_error_msg,
            raw_result=analysis,
            patch_data=patch
        )

        aggregated_data = aggregator.aggregate_metrics([metric_result])
        
        self.assertIsInstance(aggregated_data, dict)
        self.assertIn(incident_id, [item.get('incident_id') for item in aggregated_data.get('incidents', [])])

if __name__ == '__main__':
    unittest.main()