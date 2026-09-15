import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.system_health_aggregator import SystemHealthAggregator


class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.reporter_mock = MagicMock()
        self.dispatcher_mock = MagicMock()
        self.aggregator = SystemHealthAggregator(
            reporter=self.reporter_mock,
            dispatcher=self.dispatcher_mock
        )
        self.random_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_channel = f"channel_{uuid.uuid4().hex[:8]}"
        self.random_incident_id = f"inc_{random.randint(1000, 9999)}"
        self.random_message = "".join(random.choices(string.ascii_letters, k=15))
        self.random_filepath = f"/tmp/{uuid.uuid4().hex}.json"

    def test_aggregate_and_notify_success(self):
        incident_data = {
            "incident_id": self.random_incident_id,
            "error": self.random_message,
            "severity": "WARNING"
        }
        audit_summary = {"status": "failed", "score": random.randint(1, 100)}
        metrics = {"cpu_usage": random.uniform(10.0, 99.0)}
        expected_report = {"module": self.random_module, "status": "degraded"}

        self.reporter_mock.generate_health_report.return_value = expected_report
        expected_broadcast = {self.random_channel: True}
        self.dispatcher_mock.broadcast.return_value = expected_broadcast

        result = self.aggregator.aggregate_and_notify(
            self.random_module, incident_data, audit_summary, metrics
        )

        self.reporter_mock.generate_health_report.assert_called_once_with(
            self.random_module, incident_data, audit_summary, metrics
        )
        self.dispatcher_mock.broadcast.assert_called_once()
        self.assertEqual(result["report"], expected_report)
        self.assertEqual(result["broadcast_results"], expected_broadcast)

    def test_aggregate_and_notify_type_error_in_broadcast(self):
        incident_data = {"id": self.random_incident_id, "message": self.random_message}
        audit_summary = {"status": "ok"}
        metrics = {"memory": random.randint(500, 2048)}
        expected_report = {"module": self.random_module, "status": "healthy"}

        self.reporter_mock.generate_health_report.return_value = expected_report
        self.dispatcher_mock.broadcast.side_effect = TypeError("Invalid broadcast arguments")

        result = self.aggregator.aggregate_and_notify(
            self.random_module, incident_data, audit_summary, metrics
        )

        self.assertEqual(result["report"], expected_report)
        self.assertEqual(result["broadcast_results"], {})

    def test_process_stream_health_data(self):
        stream_data = f"stream_{uuid.uuid4().hex}"
        parsed_data = {
            "level": "CRITICAL",
            "incident_id": self.random_incident_id,
            "message": self.random_message
        }
        payload = {"level": "CRITICAL", "id": self.random_incident_id, "msg": self.random_message}

        self.reporter_mock.parse_stream_data.return_value = parsed_data
        self.dispatcher_mock.format_payload.return_value = payload
        self.dispatcher_mock.dispatch.return_value = True

        success = self.aggregator.process_stream_health_data(stream_data, self.random_channel)

        self.reporter_mock.parse_stream_data.assert_called_once_with(stream_data)
        self.dispatcher_mock.format_payload.assert_called_once_with(
            "CRITICAL", self.random_incident_id, self.random_message
        )
        self.dispatcher_mock.dispatch.assert_called_once_with(self.random_channel, payload)
        self.assertTrue(success)

    def test_export_comprehensive_health(self):
        health_report = {"report_id": uuid.uuid4().hex, "data": random.randint(1, 50)}
        self.reporter_mock.export_health_report.return_value = True

        res = self.aggregator.export_comprehensive_health(health_report, self.random_filepath)

        self.reporter_mock.export_health_report.assert_called_once_with(health_report, self.random_filepath)
        self.assertTrue(res)

    def test_process_and_broadcast_health(self):
        incident_data = {
            "incident_id": self.random_incident_id,
            "message": self.random_message,
            "severity": "HIGH"
        }
        audit_summary = {"audit": "passed"}
        metrics = {"latency": random.uniform(0.1, 5.0)}
        report = {"generated": True}

        self.reporter_mock.generate_health_report.return_value = report
        self.dispatcher_mock.format_payload.return_value = {"payload_key": "val"}
        self.dispatcher_mock.dispatch.return_value = False

        channels_dict = {self.random_channel: {"active": False}}
        self.dispatcher_mock.channels = channels_dict

        result = self.aggregator.process_and_broadcast_health(
            self.random_module, incident_data, audit_summary, metrics, self.random_channel, self.random_filepath
        )

        self.reporter_mock.generate_health_report.assert_called_once()
        self.reporter_mock.export_health_report.assert_called_once_with(report, self.random_filepath)
        self.assertTrue(result["dispatch_success"])
        self.assertTrue(channels_dict[self.random_channel]["active"])


class TestSystemHealthAggregatorIntegration(unittest.TestCase):

    def test_end_to_end_health_aggregation_and_dispatch(self):
        channel_name = f"chan_{uuid.uuid4().hex[:6]}"
        file_path = f"/tmp/{uuid.uuid4().hex}.json"
        module_name = f"mod_{uuid.uuid4().hex[:6]}"
        incident_id = str(random.randint(100, 999))
        error_msg = f"err_{uuid.uuid4().hex[:10]}"

        incident_data = {"incident_id": incident_id, "error": error_msg, "level": "CRITICAL"}
        audit_summary = {"passed": False}
        metrics = {"load": random.randint(80, 100)}

        aggregator = SystemHealthAggregator()
        aggregator.dispatcher.register_channel(channel_name, {"type": "console", "active": True})

        result = aggregator.process_and_broadcast_health(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            channel_name=channel_name,
            report_file_path=file_path
        )

        self.assertIn("report", result)
        self.assertIn("dispatch_success", result)

        broadcast_result = aggregator.aggregate_and_notify(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )

        self.assertIsInstance(broadcast_result, dict)
        self.assertIn("broadcast_results", broadcast_result)

        if channel_name in aggregator.dispatcher.channels:
            chan_val = aggregator.dispatcher.channels[channel_name]
            if isinstance(chan_val, dict):
                chan_val["active"] = True
            elif hasattr(chan_val, 'update'):
                chan_val.update({"active": True})

        final_broadcast = aggregator.dispatcher.broadcast({"test": uuid.uuid4().hex})
        self.assertIsInstance(final_broadcast, dict)
        self.assertIn(channel_name, final_broadcast)
        self.assertTrue(final_broadcast[channel_name])


if __name__ == '__main__':
    unittest.main()