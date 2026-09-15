import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_tracker import SystemHealthTracker
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub

class TestSystemHealthTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = SystemHealthTracker()
        self.dashboard_generator = RecoveryDashboardGenerator()
        self.aggregator = IncidentAggregator()
        self.recovery_hub = ErrorRecoveryHub()
        self.temp_files = []

    def tearDown(self):
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_tracker_to_dashboard_integration_flow(self):
        # Generate unique random identifiers to prevent hardcoding
        component_a = f"auth_service_{uuid.uuid4().hex[:6]}"
        component_b = f"payment_gateway_{uuid.uuid4().hex[:6]}"
        
        exec_time_a = round(random.uniform(0.05, 1.5), 4)
        exec_time_b = round(random.uniform(0.1, 3.0), 4)
        
        cpu_usage = round(random.uniform(10.0, 85.0), 2)
        memory_usage = round(random.uniform(128.0, 1024.0), 2)
        
        # 1. Record metrics in SystemHealthTracker
        self.tracker.record_execution_time(component_a, exec_time_a)
        self.tracker.record_execution_time(component_b, exec_time_b)
        self.tracker.record_resource_consumption(component_a, cpu_usage, memory_usage)
        
        # Record an error
        error_type = f"TimeoutException_{uuid.uuid4().hex[:4]}"
        self.tracker.record_error(component_a, error_type)
        
        # Retrieve aggregated metrics
        metrics_summary = self.tracker.get_aggregated_metrics()
        
        # Validate metrics structure and values
        self.assertIn(component_a, metrics_summary)
        self.assertIn(component_b, metrics_summary)
        self.assertAlmostEqual(metrics_summary[component_a]["last_execution_time"], exec_time_a)
        self.assertAlmostEqual(metrics_summary[component_b]["last_execution_time"], exec_time_b)
        self.assertAlmostEqual(metrics_summary[component_a]["cpu_percent"], cpu_usage)
        self.assertAlmostEqual(metrics_summary[component_a]["memory_mb"], memory_usage)
        self.assertEqual(metrics_summary[component_a]["error_count"], 1)
        
        # 2. Integrate with IncidentAggregator
        incident_id = str(uuid.uuid4())
        exception_msg = f"DatabaseConnectionFailure_{uuid.uuid4().hex[:6]}"
        traceback_sample = f"Traceback in {component_b}:\n  File 'main.py', line 42\nConnectionError"
        
        self.aggregator.process_and_aggregate(
            module_name=component_b,
            exception=Exception(exception_msg),
            traceback_str=traceback_sample,
            incident_id=incident_id
        )
        
        # 3. Integrate with RecoveryDashboardGenerator
        # We pass the tracked metrics and aggregated incidents to generate a comprehensive dashboard
        incidents_list = [
            {
                "incident_id": incident_id,
                "module": component_b,
                "error": exception_msg,
                "traceback": traceback_sample
            }
        ]
        
        reports_list = []
        
        # Generate HTML dashboard
        html_dashboard = self.dashboard_generator.generate_dashboard(
            metrics=metrics_summary,
            incidents=incidents_list,
            reports=reports_list,
            format="html"
        )
        
        # Verify dashboard contains our dynamic, random data
        self.assertIn(component_a, html_dashboard)
        self.assertIn(component_b, html_dashboard)
        self.assertIn(str(exec_time_a), html_dashboard)
        self.assertIn(str(cpu_usage), html_dashboard)
        self.assertIn(incident_id, html_dashboard)
        self.assertIn(exception_msg, html_dashboard)
        
        # 4. Export dashboard to a real file and verify existence
        temp_dir = tempfile.gettempdir()
        export_path = os.path.join(temp_dir, f"dashboard_{uuid.uuid4().hex}.html")
        self.temp_files.append(export_path)
        
        export_success = self.dashboard_generator.export_dashboard(html_dashboard, export_path)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(export_path))
        self.assertGreater(os.path.getsize(export_path), 0)
        
        # Read file to ensure content matches
        with open(export_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(component_a, file_content)
            self.assertIn(incident_id, file_content)

    def test_tracker_error_recovery_hub_integration(self):
        # Test integration with ErrorRecoveryHub when handling failures
        component_name = f"worker_node_{uuid.uuid4().hex[:6]}"
        incident_id = str(uuid.uuid4())
        exception_msg = f"OutOfMemory_{uuid.uuid4().hex[:6]}"
        traceback_str = "MemoryError: limit exceeded"
        
        # Capture failure in Recovery Hub
        self.recovery_hub.capture_failure(
            module_name=component_name,
            exception=Exception(exception_msg),
            traceback_str=traceback_str
        )
        
        # Record the error in SystemHealthTracker
        self.tracker.record_error(component_name, "OutOfMemory")
        self.tracker.record_resource_consumption(component_name, cpu_percent=99.9, memory_mb=16384.0)
        
        # Retrieve history from Recovery Hub and metrics from Tracker
        history = self.recovery_hub.get_incident_history(component_name)
        metrics = self.tracker.get_aggregated_metrics()
        
        # Verify both systems reflect the failure state of the component
        self.assertTrue(len(history) > 0)
        self.assertIn(component_name, metrics)
        self.assertEqual(metrics[component_name]["error_count"], 1)
        self.assertAlmostEqual(metrics[component_name]["cpu_percent"], 99.9)

if __name__ == "__main__":
    unittest.main()