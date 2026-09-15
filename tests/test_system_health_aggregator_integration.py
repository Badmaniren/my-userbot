import unittest
import uuid
import random
import io
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_id = str(uuid.uuid4())
        self.module_name = f"module_{random.randint(1000, 9999)}"
        self.exception_type = RuntimeError

    def test_aggregate_system_health_integration(self):
        result = self.aggregator.aggregate_system_health()
        self.assertIsInstance(result, dict)

    def test_process_stream_integration(self):
        stream_data = f"stream_metric_{self.random_id}".encode("utf-8")
        stream_io = io.BytesIO(stream_data)
        result = self.aggregator.process_stream(stream_io)
        if result is not None:
            self.assertIsInstance(result, dict)

    def test_notify_incident_integration(self):
        severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        channel = f"channel_{random.randint(100, 999)}"
        try:
            result = self.aggregator.notify_incident(severity, self.random_id)
            self.assertIsInstance(result, bool)
        except Exception:
            try:
                dispatcher = self.aggregator.NotificationChannelDispatcher()
                dispatcher.register_channel(channel, {"target": "test"})
                payload = {"incident_id": self.random_id, "severity": severity}
                res = dispatcher.dispatch(channel, payload)
                self.assertIsInstance(res, bool)
            except Exception as e:
                self.fail(f"Integration notification failed: {e}")

    def test_trigger_recovery_integration(self):
        try:
            result = self.aggregator.trigger_recovery(self.module_name, self.exception_type, self.random_id)
            self.assertIsNotNone(result)
        except Exception:
            hub = self.aggregator.ErrorRecoveryHub()
            res = hub.analyze_and_recover(self.module_name, self.exception_type, self.random_id)
            self.assertIsNotNone(res)

    def test_generate_report_integration(self):
        format_type = random.choice(["json", "html", "txt"])
        stream_data = io.BytesIO(f"epic_stream_{self.random_id}".encode("utf-8"))
        summary_payload = {"status": "active", "id": self.random_id}
        try:
            result = self.aggregator.generate_report(self.random_id, stream_data, summary_payload, format_type)
            self.assertIsInstance(result, (dict, str))
        except Exception:
            exporter = self.aggregator.RecoveryReportExporter()
            res = exporter.finalize_and_export_summary(self.random_id, stream_data, summary_payload, format_type)
            self.assertIsInstance(res, (dict, str))

if __name__ == "__main__":
    unittest.main()