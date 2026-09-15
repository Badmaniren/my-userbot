import unittest
import uuid
import random
import os
import tempfile
from io import BytesIO
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline
from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestSystemHealthAuditPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = SystemHealthAuditPipeline()
        self.monitoring_gateway = SystemHealthMonitoringGateway()
        self.notification_dispatcher = NotificationChannelDispatcher()

        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.json")
        self.dashboard_path = os.path.join(self.temp_dir.name, f"dashboard_{uuid.uuid4()}.json")
        self.stream_path = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4()}.log")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audit_pipeline_and_notifications_integration(self):
        module_name = f"module_{uuid.uuid4()}"
        random_status_code = random.choice([500, 502, 503, 504])
        
        incident_data = {
            "incident_id": str(uuid.uuid4()),
            "severity": "CRITICAL",
            "error_code": random_status_code,
            "message": f"System health failure detected: {uuid.uuid4()}"
        }
        
        audit_summary = {
            "audit_id": str(uuid.uuid4()),
            "score": round(random.uniform(0.0, 49.9), 2),
            "status": "UNHEALTHY"
        }
        
        metrics = {
            "cpu_usage": round(random.uniform(90.0, 100.0), 2),
            "memory_usage": round(random.uniform(85.0, 99.9), 2),
            "response_time_ms": random.randint(1000, 5000)
        }
        
        dashboard_format = random.choice(["json", "yaml", "html"])
        incidents_list = [str(uuid.uuid4()), str(uuid.uuid4())]
        patches_list = [str(uuid.uuid4())]

        gateway_payload = self.monitoring_gateway.capture_system_state(
            module_name=module_name,
            metrics=metrics,
            incident_data=incident_data
        )

        pipeline_result = self.pipeline.run_audit_pipeline(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertIn("telemetry", pipeline_result)
        self.assertIn("aggregation", pipeline_result)

        self.pipeline.export_and_save_pipeline_artifacts(
            payload=pipeline_result,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertTrue(os.path.exists(self.report_path), "Report file must be created by pipeline export")
        self.assertTrue(os.path.exists(self.dashboard_path), "Dashboard file must be created by pipeline export")

        channel_id = f"channel_{uuid.uuid4()}"
        notification_payload = {
            "recipient": f"admin_{uuid.uuid4()}@system.local",
            "alert_level": "CRITICAL",
            "audit_summary": audit_summary,
            "metrics": metrics,
            "incident_data": incident_data
        }

        dispatch_result = self.notification_dispatcher.dispatch_notification(
            channel_id=channel_id,
            payload=notification_payload
        )

        self.assertIsNotNone(dispatch_result, "Dispatcher must return a valid dispatch result")

    def test_audit_stream_processing_integration(self):
        stream_content = f"CRITICAL_HEALTH_ERROR:{uuid.uuid4()} - CPU:{random.randint(95, 100)}%"
        stream = BytesIO(stream_content.encode("utf-8"))

        telemetry_res, aggregator_res = self.pipeline.process_audit_stream(
            stream=stream,
            stream_path=self.stream_path
        )

        self.assertIsNotNone(telemetry_res)
        self.assertIsNotNone(aggregator_res)


if __name__ == "__main__":
    unittest.main()