import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.incident_severity_evaluator import IncidentSeverityEvaluator, evaluate_incident_severity


class TestIncidentSeverityEvaluator(unittest.TestCase):

    def setUp(self):
        self.mock_aggregator = MagicMock()
        self.mock_template_engine = MagicMock()
        self.evaluator = IncidentSeverityEvaluator(
            aggregator=self.mock_aggregator,
            template_engine=self.mock_template_engine
        )

    def test_calculate_severity_score_critical(self):
        rand_count_high = random.randint(50, 500)
        data_count = {"count": rand_count_high, "is_fatal": False}
        self.assertEqual(self.evaluator.calculate_severity_score(data_count), "CRITICAL")

        rand_count_low = random.randint(0, 49)
        data_fatal = {"count": rand_count_low, "is_fatal": True}
        self.assertEqual(self.evaluator.calculate_severity_score(data_fatal), "CRITICAL")

    def test_calculate_severity_score_high(self):
        rand_count = random.randint(26, 49)
        data = {"count": rand_count, "is_fatal": False}
        self.assertEqual(self.evaluator.calculate_severity_score(data), "HIGH")

    def test_calculate_severity_score_medium(self):
        rand_count = random.randint(6, 25)
        data = {"count": rand_count, "is_fatal": False}
        self.assertEqual(self.evaluator.calculate_severity_score(data), "MEDIUM")

    def test_calculate_severity_score_low(self):
        rand_count = random.randint(0, 5)
        data = {"count": rand_count, "is_fatal": False}
        self.assertEqual(self.evaluator.calculate_severity_score(data), "LOW")

    def test_evaluate(self):
        rand_module = uuid.uuid4().hex
        rand_exc_msg = uuid.uuid4().hex
        rand_tb = uuid.uuid4().hex
        rand_inc_id = uuid.uuid4().hex
        rand_count = random.randint(30, 40)

        agg_mock_result = {
            "incident_id": rand_inc_id,
            "count": rand_count,
            "is_fatal": False,
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        self.mock_aggregator.process_and_aggregate.return_value = agg_mock_result

        rand_payload = {"payload_key": uuid.uuid4().hex}
        self.mock_template_engine.generate_notification_payload.return_value = rand_payload

        exc = Exception(rand_exc_msg)
        result = self.evaluator.evaluate(rand_module, exc, rand_tb, rand_inc_id)

        self.mock_aggregator.process_and_aggregate.assert_called_once_with(
            rand_module, exc, rand_tb, rand_inc_id
        )
        self.assertEqual(result["incident_id"], rand_inc_id)
        self.assertEqual(result["severity"], "HIGH")
        self.assertEqual(result["payload"], rand_payload)
        self.assertEqual(result["aggregated_data"], agg_mock_result)

    def test_evaluate_stream(self):
        rand_stream_data = uuid.uuid4().hex
        rand_parsed_id = uuid.uuid4().hex
        rand_freq = random.randint(60, 100)

        parsed_mock_result = {
            "incident_id": rand_parsed_id,
            "frequency": rand_freq
        }
        self.mock_template_engine.parse_stream_data.return_value = parsed_mock_result

        rand_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_template_engine.generate_notification_payload.return_value = rand_payload

        result = self.evaluator.evaluate_stream(uuid.uuid4().hex, rand_stream_data)

        self.mock_template_engine.parse_stream_data.assert_called_once_with(rand_stream_data)
        self.assertEqual(result["incident_id"], rand_parsed_id)
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertEqual(result["payload"], rand_payload)

    def test_evaluate_and_notify(self):
        rand_module = uuid.uuid4().hex
        rand_exc_msg = uuid.uuid4().hex
        rand_tb = uuid.uuid4().hex
        rand_inc_id = uuid.uuid4().hex

        with patch.object(self.evaluator, 'evaluate') as mock_eval:
            rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            rand_agg_data = {uuid.uuid4().hex: uuid.uuid4().hex}
            rand_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
            rand_notification = {uuid.uuid4().hex: uuid.uuid4().hex}

            mock_eval.return_value = {
                "incident_id": rand_inc_id,
                "severity": rand_severity,
                "payload": rand_payload,
                "aggregated_data": rand_agg_data
            }

            self.mock_template_engine.generate_notification_payload.return_value = rand_notification

            exc = Exception(rand_exc_msg)
            res = self.evaluator.evaluate_and_notify(rand_module, exc, rand_tb, rand_inc_id)

            mock_eval.assert_called_once_with(rand_module, exc, rand_tb, rand_inc_id)
            self.mock_template_engine.generate_notification_payload.assert_called_with(
                rand_severity, rand_inc_id, rand_agg_data
            )
            self.assertEqual(res["incident_id"], rand_inc_id)
            self.assertEqual(res["severity"], rand_severity)
            self.assertEqual(res["notification"], rand_notification)
            self.assertEqual(res["payload"], rand_payload)
            self.assertEqual(res["aggregated_data"], rand_agg_data)

    def test_export_incident_report(self):
        rand_template = uuid.uuid4().hex
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_output_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        rand_format = random.choice(["html", "json", "pdf"])
        rand_export_res = uuid.uuid4().hex

        self.mock_template_engine.export_notification_file.return_value = rand_export_res

        res = self.evaluator.export_incident_report(rand_template, rand_context, rand_output_path, rand_format)

        self.mock_template_engine.render_template.assert_called_once_with(
            rand_template, rand_context, rand_format
        )
        self.mock_template_engine.export_notification_file.assert_called_once_with(
            rand_context, rand_output_path
        )
        self.assertEqual(res, rand_export_res)

    def test_global_evaluate_incident_severity_function(self):
        rand_module = uuid.uuid4().hex
        rand_exc_msg = uuid.uuid4().hex
        rand_tb = uuid.uuid4().hex
        rand_inc_id = uuid.uuid4().hex

        with patch('skills.incident_severity_evaluator.IncidentSeverityEvaluator') as mock_evaluator_class:
            mock_instance = mock_evaluator_class.return_value
            rand_return_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_instance.evaluate.return_value = rand_return_dict

            exc = Exception(rand_exc_msg)
            res = evaluate_incident_severity(rand_module, exc, rand_tb, rand_inc_id)

            mock_evaluator_class.assert_called_once()
            mock_instance.evaluate.assert_called_once_with(rand_module, exc, rand_tb, rand_inc_id)
            self.assertEqual(res, rand_return_dict)

if __name__ == '__main__':
    unittest.main()