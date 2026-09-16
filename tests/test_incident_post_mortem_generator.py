import unittest
from unittest.mock import patch
import os
import uuid
import random
import io
from skills.incident_post_mortem_generator import (
    IncidentSeverityEvaluator,
    IncidentPostMortemGenerator,
    generate_incident_post_mortem
)


class TestIncidentSeverityEvaluator(unittest.TestCase):
    def test_re_evaluate_critical_impact(self):
        evaluator = IncidentSeverityEvaluator()
        random_impact = random.randint(81, 200)
        incident_data = {"impact_score": random_impact, "severity": "SEV-2"}
        trend_data = {"recurrence_rate": 0.1}
        recovery_data = {"failed_attempts": 0}

        result = evaluator.re_evaluate(incident_data, trend_data, recovery_data)
        self.assertEqual(result, "CRITICAL")

    def test_re_evaluate_critical_recurrence(self):
        evaluator = IncidentSeverityEvaluator()
        random_recurrence = round(random.uniform(0.91, 1.0), 2)
        incident_data = {"impact_score": 10, "severity": "SEV-3"}
        trend_data = {"recurrence_rate": random_recurrence}
        recovery_data = {"failed_attempts": 0}

        result = evaluator.re_evaluate(incident_data, trend_data, recovery_data)
        self.assertEqual(result, "CRITICAL")

    def test_re_evaluate_critical_failed_attempts(self):
        evaluator = IncidentSeverityEvaluator()
        random_failures = random.randint(2, 10)
        incident_data = {"impact_score": 5, "severity": "SEV-3"}
        trend_data = {"recurrence_rate": 0.0}
        recovery_data = {"failed_attempts": random_failures}

        result = evaluator.re_evaluate(incident_data, trend_data, recovery_data)
        self.assertEqual(result, "CRITICAL")

    def test_re_evaluate_non_critical(self):
        evaluator = IncidentSeverityEvaluator()
        random_severity = f"SEV-{random.randint(1, 5)}"
        incident_data = {"impact_score": random.randint(0, 80), "severity": random_severity}
        trend_data = {"recurrence_rate": round(random.uniform(0.0, 0.89), 2)}
        recovery_data = {"failed_attempts": random.randint(0, 1)}

        result = evaluator.re_evaluate(incident_data, trend_data, recovery_data)
        self.assertEqual(result, random_severity)


class TestIncidentPostMortemGenerator(unittest.TestCase):
    def test_generate_post_mortem_standard(self):
        incident_id = uuid.uuid4().hex
        severity_val = f"SEV-{random.randint(1, 4)}"
        error_code = f"ERR_{uuid.uuid4().hex[:6]}"
        description = f"Desc_{uuid.uuid4().hex}"
        export_return_path = f"/var/log/{uuid.uuid4().hex}.json"

        mock_aggregator = unittest.mock.Mock()
        mock_aggregator.get_incident.return_value = {
            "incident_id": incident_id,
            "severity": severity_val,
            "error_code": error_code,
            "description": description,
            "impact_score": random.randint(0, 50)
        }

        mock_trend_analyzer = unittest.mock.Mock()
        trend_payload = {"recurrence_rate": 0.1, "trend": uuid.uuid4().hex}
        mock_trend_analyzer.analyze_trends.return_value = trend_payload

        mock_recovery_hub = unittest.mock.Mock()
        recovery_payload = {"failed_attempts": 0, "actions": uuid.uuid4().hex}
        mock_recovery_hub.get_recovery_history.return_value = recovery_payload

        mock_exporter = unittest.mock.Mock()
        mock_exporter.export.return_value = export_return_path

        generator = IncidentPostMortemGenerator(
            incident_aggregator=mock_aggregator,
            incident_trend_analyzer=mock_trend_analyzer,
            error_recovery_hub=mock_recovery_hub,
            recovery_report_exporter=mock_exporter
        )

        payload = generator.generate(incident_id, include_raw_telemetry=False)

        self.assertEqual(payload["incident_id"], incident_id)
        self.assertEqual(payload["severity"], severity_val)
        self.assertEqual(payload["trends"], trend_payload)
        self.assertEqual(payload["recovery_actions"], recovery_payload)
        self.assertEqual(payload["export_path"], export_return_path)
        self.assertNotIn("telemetry_hash", payload)
        mock_exporter.export.assert_called_once()

    def test_generate_post_mortem_with_telemetry(self):
        incident_id = uuid.uuid4().hex
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        telemetry_content = uuid.uuid4().bytes
        export_return_path = f"/var/log/{uuid.uuid4().hex}.json"

        mock_aggregator = unittest.mock.Mock()
        mock_aggregator.get_incident.return_value = {
            "incident_id": incident_id,
            "severity": "SEV-1",
            "impact_score": 90,
            "log_pointer": log_path
        }

        mock_trend_analyzer = unittest.mock.Mock()
        mock_trend_analyzer.analyze_trends.return_value = {"recurrence_rate": 0.95}

        mock_recovery_hub = unittest.mock.Mock()
        mock_recovery_hub.get_recovery_history.return_value = {"failed_attempts": 3}

        mock_exporter = unittest.mock.Mock()
        mock_exporter.export.return_value = export_return_path

        generator = IncidentPostMortemGenerator(
            incident_aggregator=mock_aggregator,
            incident_trend_analyzer=mock_trend_analyzer,
            error_recovery_hub=mock_recovery_hub,
            recovery_report_exporter=mock_exporter
        )

        fake_file = io.BytesIO(telemetry_content)
        with patch("builtins.open", return_value=fake_file):
            payload = generator.generate(incident_id, include_raw_telemetry=True)

        self.assertEqual(payload["final_severity"], "CRITICAL")
        self.assertIn("telemetry_hash", payload)
        self.assertEqual(payload["export_path"], export_return_path)


class TestGenerateIncidentPostMortemFunction(unittest.TestCase):
    def test_generate_incident_post_mortem_file_creation(self):
        incident_id = uuid.uuid4().hex
        error_code = f"CODE_{uuid.uuid4().hex[:5]}"
        severity = f"SEV-{random.randint(1, 3)}"
        description = f"Description_{uuid.uuid4().hex}"
        trend_data = f"Trend_{uuid.uuid4().hex}"
        recovery_history = f"Recovery_{uuid.uuid4().hex}"

        output_path = f"/tmp/{uuid.uuid4().hex}/post_mortem_{uuid.uuid4().hex}.md"

        aggregated_data = {
            "error_code": error_code,
            "severity": severity,
            "description": description
        }

        with patch("os.makedirs") as mock_makedirs, patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = generate_incident_post_mortem(
                incident_id, aggregated_data, trend_data, recovery_history, output_path
            )

            self.assertEqual(res_path, output_path)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once_with(output_path, "w", encoding="utf-8")

            handle = mock_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn(incident_id, written_content)
            self.assertIn(error_code, written_content)
            self.assertIn(severity, written_content)
            self.assertIn(description, written_content)
            self.assertIn(trend_data, written_content)
            self.assertIn(recovery_history, written_content)


if __name__ == "__main__":
    unittest.main()