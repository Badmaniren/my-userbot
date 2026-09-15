import io
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.incident_severity_evaluator import (
    IncidentSeverityEvaluator,
    evaluate_incident_severity,
)


def _gen_random_str(prefix: str = "") -> str:
    token = uuid.uuid4().hex[: random.randint(8, 16)]
    return f"{prefix}_{token}" if prefix else token


def _gen_random_dict() -> dict:
    return {
        _gen_random_str("key"): _gen_random_str("val")
        for _ in range(random.randint(2, 5))
    }


class TestIncidentSeverityEvaluator(unittest.TestCase):
    def setUp(self):
        self.random_module_name = _gen_random_str("module")
        self.random_incident_id = _gen_random_str("inc")
        self.random_error_msg = _gen_random_str("error")
        self.random_traceback = (
            f"Traceback (most recent call last):\n  File '{_gen_random_str()}', line {random.randint(1, 100)}\n"
            f"ValueError: {self.random_error_msg}"
        )
        self.random_exception = ValueError(self.random_error_msg)

    def test_evaluator_initialization_defaults(self):
        with patch("skills.incident_severity_evaluator.IncidentAggregator") as mock_agg_cls, \
             patch("skills.incident_severity_evaluator.NotificationTemplateEngine") as mock_engine_cls:
            evaluator = IncidentSeverityEvaluator()

            mock_agg_cls.assert_called_once()
            mock_engine_cls.assert_called_once()
            self.assertIsNotNone(evaluator.aggregator)
            self.assertIsNotNone(evaluator.template_engine)

    def test_evaluator_initialization_injected_dependencies(self):
        custom_aggregator = MagicMock()
        custom_engine = MagicMock()

        evaluator = IncidentSeverityEvaluator(
            aggregator=custom_aggregator,
            template_engine=custom_engine,
        )

        self.assertIs(evaluator.aggregator, custom_aggregator)
        self.assertIs(evaluator.template_engine, custom_engine)

    def test_evaluate_incident_severity_critical(self):
        mock_aggregator = MagicMock()
        mock_engine = MagicMock()

        occurrences = random.randint(50, 100)
        agg_result = {
            "incident_id": self.random_incident_id,
            "module": self.random_module_name,
            "count": occurrences,
            "status": _gen_random_str("status"),
        }
        mock_aggregator.process_and_aggregate.return_value = agg_result

        expected_rendered_text = _gen_random_str("CRITICAL_NOTIFICATION")
        expected_payload = {
            "notification_id": _gen_random_str("notif"),
            "severity": "CRITICAL",
            "rendered": expected_rendered_text,
        }
        mock_engine.generate_notification_payload.return_value = expected_payload
        mock_engine.render_text.return_value = expected_rendered_text

        evaluator = IncidentSeverityEvaluator(
            aggregator=mock_aggregator,
            template_engine=mock_engine,
        )

        result = evaluator.evaluate(
            module_name=self.random_module_name,
            exception=self.random_exception,
            traceback_str=self.random_traceback,
            incident_id=self.random_incident_id,
        )

        mock_aggregator.process_and_aggregate.assert_called_once_with(
            self.random_module_name,
            self.random_exception,
            self.random_traceback,
            self.random_incident_id,
        )

        mock_engine.generate_notification_payload.assert_called_once()
        call_args, _ = mock_engine.generate_notification_payload.call_args
        self.assertIn("CRITICAL", str(call_args))

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("severity"), "CRITICAL")
        self.assertEqual(result.get("incident_id"), self.random_incident_id)
        self.assertEqual(result.get("payload"), expected_payload)

    def test_evaluate_incident_severity_low_and_medium(self):
        mock_aggregator = MagicMock()
        mock_engine = MagicMock()

        low_count = random.randint(1, 4)
        mock_aggregator.process_and_aggregate.return_value = {
            "incident_id": self.random_incident_id,
            "module": self.random_module_name,
            "count": low_count,
        }
        mock_engine.generate_notification_payload.side_effect = (
            lambda severity, inc_id, raw: {"severity": severity, "incident_id": inc_id, "data": raw}
        )

        evaluator = IncidentSeverityEvaluator(
            aggregator=mock_aggregator,
            template_engine=mock_engine,
        )

        low_result = evaluator.evaluate(
            module_name=self.random_module_name,
            exception=self.random_exception,
            traceback_str=self.random_traceback,
            incident_id=self.random_incident_id,
        )
        self.assertEqual(low_result.get("severity"), "LOW")

        med_count = random.randint(10, 25)
        mock_aggregator.process_and_aggregate.return_value = {
            "incident_id": self.random_incident_id,
            "module": self.random_module_name,
            "count": med_count,
        }

        med_result = evaluator.evaluate(
            module_name=self.random_module_name,
            exception=self.random_exception,
            traceback_str=self.random_traceback,
            incident_id=self.random_incident_id,
        )
        self.assertEqual(med_result.get("severity"), "MEDIUM")

    def test_evaluate_stream_uses_io_bytes(self):
        mock_aggregator = MagicMock()
        mock_engine = MagicMock()

        random_stream_content = _gen_random_str("stream_log_payload").encode("utf-8")
        stream_input = io.BytesIO(random_stream_content)

        parsed_stream_dict = {
            "parsed_id": self.random_incident_id,
            "error": self.random_error_msg,
            "frequency": random.randint(5, 15),
        }
        mock_engine.parse_stream_data.return_value = parsed_stream_dict
        mock_engine.generate_notification_payload.return_value = {
            "result": "OK",
            "token": _gen_random_str("token"),
        }

        evaluator = IncidentSeverityEvaluator(
            aggregator=mock_aggregator,
            template_engine=mock_engine,
        )

        stream_result = evaluator.evaluate_stream(
            module_name=self.random_module_name,
            stream_data=stream_input,
        )

        mock_engine.parse_stream_data.assert_called_once_with(stream_input)
        self.assertIsInstance(stream_result, dict)
        self.assertEqual(stream_result.get("incident_id"), self.random_incident_id)
        self.assertIn("severity", stream_result)

    def test_calculate_severity_score_logic(self):
        evaluator = IncidentSeverityEvaluator(
            aggregator=MagicMock(),
            template_engine=MagicMock(),
        )

        critical_data = {"count": random.randint(50, 200), "is_fatal": True}
        high_data = {"count": random.randint(26, 49), "is_fatal": False}
        medium_data = {"count": random.randint(6, 25), "is_fatal": False}
        low_data = {"count": random.randint(1, 5), "is_fatal": False}

        self.assertEqual(evaluator.calculate_severity_score(critical_data), "CRITICAL")
        self.assertEqual(evaluator.calculate_severity_score(high_data), "HIGH")
        self.assertEqual(evaluator.calculate_severity_score(medium_data), "MEDIUM")
        self.assertEqual(evaluator.calculate_severity_score(low_data), "LOW")

    def test_evaluate_incident_severity_module_level_function(self):
        with patch("skills.incident_severity_evaluator.IncidentSeverityEvaluator") as mock_evaluator_cls:
            mock_instance = MagicMock()
            mock_evaluator_cls.return_value = mock_instance

            expected_output = {
                "incident_id": self.random_incident_id,
                "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "marker": _gen_random_str("marker"),
            }
            mock_instance.evaluate.return_value = expected_output

            res = evaluate_incident_severity(
                module_name=self.random_module_name,
                exception=self.random_exception,
                traceback_str=self.random_traceback,
                incident_id=self.random_incident_id,
            )

            mock_evaluator_cls.assert_called_once()
            mock_instance.evaluate.assert_called_once_with(
                self.random_module_name,
                self.random_exception,
                self.random_traceback,
                self.random_incident_id,
            )
            self.assertEqual(res, expected_output)

    def test_render_and_export_notification_pipeline(self):
        mock_aggregator = MagicMock()
        mock_engine = MagicMock()

        random_template = _gen_random_str("template_name")
        random_file_path = f"/tmp/{_gen_random_str('path')}.html"
        rendered_html = f"<html><body>{_gen_random_str('body')}</body></html>"

        mock_engine.render_template.return_value = rendered_html
        mock_engine.export_notification_file.return_value = True

        evaluator = IncidentSeverityEvaluator(
            aggregator=mock_aggregator,
            template_engine=mock_engine,
        )

        context_data = _gen_random_dict()
        exported = evaluator.export_incident_report(
            template_name=random_template,
            context=context_data,
            output_path=random_file_path,
            format_type="html",
        )

        self.assertTrue(exported)
        mock_engine.render_template.assert_called_once_with(
            random_template,
            context_data,
            "html",
        )
        mock_engine.export_notification_file.assert_called_once_with(
            context_data,
            random_file_path,
        )

    def test_graceful_handling_on_empty_traceback_and_none_id(self):
        mock_aggregator = MagicMock()
        mock_engine = MagicMock()

        generated_id = _gen_random_str("auto_id")
        mock_aggregator.process_and_aggregate.side_effect = (
            lambda m, e, t, i: {"incident_id": i or generated_id, "count": 1}
        )
        mock_engine.generate_notification_payload.return_value = {"status": "ok"}

        evaluator = IncidentSeverityEvaluator(
            aggregator=mock_aggregator,
            template_engine=mock_engine,
        )

        result = evaluator.evaluate(
            module_name=self.random_module_name,
            exception=self.random_exception,
            traceback_str="",
            incident_id=None,
        )

        self.assertIsInstance(result, dict)
        self.assertIn("severity", result)
        self.assertIsNotNone(result.get("incident_id"))


if __name__ == "__main__":
    unittest.main()