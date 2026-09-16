import unittest
import uuid
import random
import json
import os
import io

from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.system_health_aggregator import system_health_aggregator
from skills.incident_post_mortem_report_builder import (
    IncidentPostMortemReportBuilder,
    incident_post_mortem_report_builder
)


class TestIncidentPostMortemReportBuilderIntegration(unittest.TestCase):

    def test_end_to_end_post_mortem_report_pipeline(self):
        random_suffix = str(uuid.uuid4())
        test_incident_id = f"inc-{random.randint(1000, 9999)}-{random_suffix[:8]}"

        mock_incident_data = {
            "incident_id": test_incident_id,
            "description": f"Integration test critical failure {random.random()}",
            "status": "investigating"
        }

        incident_aggregator[test_incident_id] = mock_incident_data

        builder = IncidentPostMortemReportBuilder(
            incident_aggregator=incident_aggregator,
            incident_severity_evaluator=incident_severity_evaluator,
            incident_trend_analyzer=incident_trend_analyzer,
            system_health_telemetry_collector=system_health_aggregator
        )

        report = builder.build_report(test_incident_id)

        self.assertIn("incident_details", report)
        self.assertIn("severity_assessment", report)
        self.assertIn("trend_analysis", report)
        self.assertIn("system_telemetry", report)

        self.assertEqual(report["incident_details"]["incident_id"], test_incident_id)

        stream = io.BytesIO()
        exported_stream = builder.export_report_stream(test_incident_id, stream)
        exported_stream.seek(0)
        loaded_content = json.loads(exported_stream.read().decode('utf-8'))

        self.assertEqual(loaded_content["incident_details"]["incident_id"], test_incident_id)

        functional_input_data = {
            "incident": report["incident_details"],
            "severity": report["severity_assessment"],
            "trend": report["trend_analysis"],
            "health": report["system_telemetry"]
        }

        func_result = incident_post_mortem_report_builder(functional_input_data)

        self.assertIn("report_id", func_result)
        self.assertIn("file_path", func_result)

        file_path = func_result["file_path"]
        self.assertTrue(os.path.exists(file_path))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            self.assertEqual(file_data["incident_details"]["incident_id"], test_incident_id)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


if __name__ == "__main__":
    unittest.main()