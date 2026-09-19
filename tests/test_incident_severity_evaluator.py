import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.incident_severity_evaluator import (
    IncidentSeverityEvaluator,
    evaluate_incident_severity
)


class TestIncidentSeverityEvaluator(unittest.TestCase):

    def setUp(self):
        self.mock_aggregator = MagicMock()
        self.mock_template_engine = MagicMock()
        self.evaluator = IncidentSeverityEvaluator(
            aggregator=self.mock_aggregator,
            template_engine=self.mock_template_engine
        )

    def test_calculate_severity_score_critical_by_count(self):
        count = random.randint(50, 1000)
        data = {"count": count, "is_fatal": False}
        score = self.evaluator.calculate_severity_score(data)
        self.assertEqual(score, "CRITICAL")

    def test_calculate_severity_score_critical_by_fatal(self):
        count = random.randint(0, 49)
        data = {"count": count, "is_fatal": True}
        score = self.evaluator.calculate_severity_score(data)
        self.assertEqual(score, "CRITICAL")

    def test_calculate_severity_score_high(self):
        count = random.randint(26, 49)
        data = {"count": count, "is_fatal": False}
        score = self.evaluator.calculate_severity_score(data)
        self.assertEqual(score, "HIGH")

    def test_calculate_severity_score_medium(self):
        count = random.randint(6, 25)
        data = {"count": count, "is_fatal": False}
        score = self.evaluator.calculate_severity_score(data)
        self.assertEqual(score, "MEDIUM")

    def test_calculate_severity_score_low(self):
        count = random.randint(0, 5)
        data = {"count": count, "is_fatal": False}
        score = self.evaluator.calculate_severity_score(data)
        self.assertEqual(score, "LOW")

    def test_evaluate(self):
        mod_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        exc_msg = ''.join(random.choices(string.ascii_letters, k=15))
        exc = Exception(exc_msg)
        tb_str = ''.join(random.choices(string.ascii_letters, k=20))
        inc_id = uuid.uuid4().hex

        agg_return = {
            "count": random.randint(6, 25),
            "is_fatal": False,
            "incident_id": inc_id
        }
        self.mock_aggregator.process_and_aggregate.return_value = agg_return

        payload_return = {"payload_id": uuid.uuid4().hex}
        self.mock_template_engine.generate_notification_payload.return_value = payload_return

        result = self.evaluator.evaluate(mod_name, exc, tb_str, inc_id)

        self.mock_aggregator.process_and_aggregate.assert_called_once_with(
            mod_name, exc, tb_str, inc_id
        )
        self.mock_template_engine.generate_notification_payload.assert_called_once_with(
            "MEDIUM", inc_id, agg_return
        )

        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["severity"], "MEDIUM")
        self.assertEqual(result["payload"], payload_return)
        self.assertEqual(result["aggregated_data"], agg_return)

    def test_evaluate_stream(self):
        stream_data = {'raw_stream': uuid.uuid4().hex}
        parsed_id = uuid.uuid4().hex
        freq = random.randint(26, 49)

        parsed_return = {
            "parsed_id": parsed_id,
            "frequency": freq
        }
        self.mock_template_engine.parse_stream_data.return_value = parsed_return

        payload_return = {"stream_payload": uuid.uuid4().hex}
        self.mock_template_engine.generate_notification_payload.return_value = payload_return

        mod_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        result = self.evaluator.evaluate_stream(mod_name, stream_data)

        self.mock_template_engine.parse_stream_data.assert_called_once_with(stream_data)
        self.mock_template_engine.generate_notification_payload.assert_called_once_with(
            "HIGH", parsed_id, parsed_return
        )

        self.assertEqual(result["incident_id"], parsed_id)
        self.assertEqual(result["severity"], "HIGH")
        self.assertEqual(result["payload"], payload_return)

    def test_evaluate_and_notify(self):
        mod_name = ''.join(random.choices(string.ascii_lowercase, k=9))
        exc = RuntimeError(''.join(random.choices(string.ascii_letters, k=10)))
        tb_str = ''.join(random.choices(string.ascii_letters, k=12))
        inc_id = uuid.uuid4().hex

        agg_return = {
            "count": 60,
            "is_fatal": True,
            "incident_id": inc_id
        }
        self.mock_aggregator.process_and_aggregate.return_value = agg_return

        payload_1 = {"type": uuid.uuid4().hex}
        payload_2 = {"type": uuid.uuid4().hex}
        self.mock_template_engine.generate_notification_payload.side_effect = [payload_1, payload_2]

        result = self.evaluator.evaluate_and_notify(mod_name, exc, tb_str, inc_id)

        self.assertEqual(result["incident_id"], inc_id)
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertEqual(result["payload"], payload_1)
        self.assertEqual(result["notification"], payload_2)
        self.assertEqual(result["aggregated_data"], agg_return)

    def test_export_incident_report(self):
        tpl_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        out_path = f"/tmp/{uuid.uuid4().hex}.html"
        fmt = "html"

        expected_export_result = uuid.uuid4().hex
        self.mock_template_engine.export_notification_file.return_value = expected_export_result

        res = self.evaluator.export_incident_report(tpl_name, context, out_path, fmt)

        self.mock_template_engine.render_template.assert_called_once_with(tpl_name, context, fmt)
        self.mock_template_engine.export_notification_file.assert_called_once_with(context, out_path)
        self.assertEqual(res, expected_export_result)

    def test_evaluate_incident_severity_helper(self):
        mod_name = ''.join(random.choices(string.ascii_lowercase, k=7))
        exc = ValueError(uuid.uuid4().hex)
        tb_str = uuid.uuid4().hex
        inc_id = uuid.uuid4().hex

        with patch("skills.incident_severity_evaluator.IncidentSeverityEvaluator") as mock_evaluator_cls:
            mock_instance = mock_evaluator_cls.return_value
            expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_instance.evaluate.return_value = expected_dict

            res = evaluate_incident_severity(mod_name, exc, tb_str, inc_id)

            mock_evaluator_cls.assert_called_once()
            mock_instance.evaluate.assert_called_once_with(mod_name, exc, tb_str, inc_id)
            self.assertEqual(res, expected_dict)