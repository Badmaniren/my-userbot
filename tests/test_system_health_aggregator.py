import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.error_msg = f"error_{uuid.uuid4().hex[:8]}"
        self.incident_id = uuid.uuid4().hex
        self.audit_data = {f"key_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        self.channel = f"channel_{uuid.uuid4().hex[:6]}"
        self.payload = {f"metric_{uuid.uuid4().hex[:4]}": random.random()}

    def test_calculate_health_index(self):
        expected_health = {f"status_{uuid.uuid4().hex[:4]}": f"val_{uuid.uuid4().hex[:4]}"}

        with patch.object(self.aggregator.incident_aggregator, 'process_and_aggregate') as mock_process, \
             patch.object(self.aggregator.dashboard_generator, 'aggregate_system_health', return_value=expected_health) as mock_aggregate:

            result = self.aggregator.calculate_health_index(self.module_name)

            mock_process.assert_called_once_with(self.module_name, "", "", "")
            mock_aggregate.assert_called_once_with(self.module_name)
            self.assertEqual(result, expected_health)

    def test_process_incoming_stream(self):
        stream_content = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(stream_content)
        expected_parsed = {f"parsed_{uuid.uuid4().hex[:4]}": random.randint(10, 50)}

        with patch.object(self.aggregator.dashboard_generator, 'parse_stream_data', return_value=expected_parsed) as mock_parse:
            result = self.aggregator.process_incoming_stream(stream)

            mock_parse.assert_called_once_with(stream)
            self.assertEqual(result, expected_parsed)

    def test_generate_full_report(self):
        expected_report = f"report_content_{uuid.uuid4().hex}"

        with patch.object(self.aggregator.report_exporter, 'generate_comprehensive_report', return_value=expected_report) as mock_generate:
            result = self.aggregator.generate_full_report(
                self.module_name,
                self.error_msg,
                self.incident_id,
                self.audit_data
            )

            mock_generate.assert_called_once_with(
                self.module_name,
                self.error_msg,
                self.aggregator.incident_aggregator,
                self.incident_id,
                self.audit_data
            )
            self.assertEqual(result, expected_report)

    def test_notify_stakeholders(self):
        expected_success = random.choice([True, False])

        with patch.object(self.aggregator.notification_dispatcher, 'dispatch', return_value=expected_success) as mock_dispatch:
            result = self.aggregator.notify_stakeholders(self.channel, self.payload)

            mock_dispatch.assert_called_once_with(self.channel, self.payload)
            self.assertEqual(result, expected_success)

    def test_execute_recovery_sequence(self):
        patch_payload = {f"patch_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}
        mock_arg = MagicMock()
        expected_result = random.choice([True, False])

        with patch.object(self.aggregator.patch_scheduler, 'coordinate_and_schedule', return_value=expected_result) as mock_coordinate:
            result = self.aggregator.execute_recovery_sequence(self.incident_id, patch_payload, mock_arg)

            mock_coordinate.assert_called_once_with(self.incident_id, patch_payload, mock_arg)
            self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()