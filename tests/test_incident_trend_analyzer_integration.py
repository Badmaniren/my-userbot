import unittest
import uuid
import random
from skills.incident_trend_analyzer import IncidentTrendAnalyzer, start_new
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator

class TestIncidentTrendAnalyzerIntegration(unittest.TestCase):
    def test_trend_analyzer_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        module_name = f"test_module_{random_suffix}"
        incident_id = uuid.uuid4().hex
        
        hub = ErrorRecoveryHub()
        aggregator = IncidentAggregator()
        analyzer = IncidentTrendAnalyzer()
        
        try:
            raise RuntimeError(f"Integration error {random_suffix}")
        except Exception as e:
            tb_str = "Traceback (most recent call last):\n  File test.py"
            
            agg_result = aggregator.process_and_aggregate(
                module_name=module_name,
                exception=e,
                traceback_str=tb_str,
                incident_id=incident_id
            )
            
            failure_capture = hub.capture_failure(
                module_name=module_name,
                exception=e,
                traceback_str=tb_str
            )
            
            trend_result = analyzer.analyze_trends(module_name)
            
            start_result = start_new(
                success=True,
                incident_id=incident_id,
                raw_result=trend_result
            )
            
            self.assertEqual(trend_result["module_name"], module_name)
            self.assertIn("status", trend_result)
            self.assertIn("trend", trend_result)
            
            self.assertEqual(start_result["incident_id"], incident_id)
            self.assertTrue(start_result["success"])
            self.assertEqual(start_result["raw_result"], trend_result)

if __name__ == "__main__":
    unittest.main()