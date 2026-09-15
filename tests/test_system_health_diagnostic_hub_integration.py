import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_diagnostic_hub import system_health_diagnostic_hub
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.system_health_aggregator import system_health_aggregator
from skills.system_health_reporter import system_health_reporter

class TestSystemHealthDiagnosticHubIntegration(unittest.TestCase):
    def test_diagnostic_hub_real_pipeline(self):
        random_node_id = f"node-{uuid.uuid4()}"
        random_cpu_load = round(random.uniform(85.0, 99.9), 2)
        random_error_code = random.randint(500, 599)
        
        telemetry_payload = {
            "node_id": random_node_id,
            "metrics": {
                "cpu_usage": random_cpu_load,
                "error_status": random_error_code
            },
            "timestamp": uuid.uuid4().hex
        }

        collected_data = system_health_telemetry_collector(telemetry_payload)
        self.assertIsNotNone(collected_data)

        aggregated_data = system_health_aggregator(collected_data)
        self.assertIn(random_node_id, str(aggregated_data))

        diagnostic_result = system_health_diagnostic_hub(aggregated_data)
        self.assertIsInstance(diagnostic_result, dict)
        self.assertIn("anomaly_detected", diagnostic_result)
        self.assertTrue(diagnostic_result["anomaly_detected"])

        with tempfile.TemporaryDirectory() as temp_dir:
            report_filename = f"report_{uuid.uuid4()}.txt"
            report_path = os.path.join(temp_dir, report_filename)
            
            export_status = system_health_reporter(diagnostic_result, output_path=report_path)
            
            self.assertTrue(export_status)
            self.assertTrue(os.path.exists(report_path))
            
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(random_node_id, content)
                self.assertIn(str(random_error_code), content)

if __name__ == "__main__":
    unittest.main()