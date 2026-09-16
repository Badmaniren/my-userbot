import unittest
import uuid
import random
import os
from skills.incident_sla_violation_analyzer import IncidentSlaviolationAnalyzer
from skills.incident_sla_tracker import IncidentSlaTracker
from skills.incident_sla_breach_predictor import IncidentSlaBreachPredictor
from skills.incident_aggregator import IncidentAggregator

class TestIncidentSlaviolationAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentSlaviolationAnalyzer()
        self.tracker = IncidentSlaTracker()
        self.predictor = IncidentSlaBreachPredictor()
        self.aggregator = IncidentAggregator()

    def test_sla_violation_analyzer_end_to_end(self):
        random_suffix = str(uuid.uuid4())[:8]
        incident_id = f"INC-{random_suffix}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        resolution_time_actual = random.randint(120, 3600)
        resolution_time_target = random.randint(60, 1800)

        incident_data = {
            "incident_id": incident_id,
            "severity": severity_level,
            "actual_time": resolution_time_actual,
            "target_time": resolution_time_target,
            "status": "BREACHED"
        }

        aggregated_incident = self.aggregator.aggregate(incident_data)
        self.assertIsNotNone(aggregated_incident)

        tracked_sla = self.tracker.track(incident_id, resolution_time_actual, resolution_time_target)
        self.assertEqual(tracked_sla.get("incident_id"), incident_id)

        prediction_metrics = self.predictor.evaluate(incident_id)
        self.assertIsInstance(prediction_metrics, dict)

        analysis_report = self.analyzer.analyze_root_causes(
            incident_id=incident_id,
            incident_data=aggregated_incident,
            prediction_metrics=prediction_metrics
        )

        self.assertIn("root_causes", analysis_report)
        self.assertIn("actionable_insights", analysis_report)
        self.assertEqual(analysis_report.get("analyzed_incident_id"), incident_id)

        report_file_path = f"sla_analysis_{incident_id}.json"
        if os.path.exists(report_file_path):
            self.assertTrue(os.path.isfile(report_file_path))
            try:
                os.remove(report_file_path)
            except OSError:
                pass

if __name__ == "__main__":
    unittest.main()