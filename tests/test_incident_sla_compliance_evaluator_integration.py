import unittest
import uuid
import random
import os
from skills.incident_sla_compliance_evaluator import IncidentSLAComplianceEvaluator
from skills.incident_aggregator import IncidentAggregator
from skills.incident_sla_tracker import IncidentSLATracker
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline

class TestIncidentSLAComplianceEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.evaluator = IncidentSLAComplianceEvaluator()
        self.aggregator = IncidentAggregator()
        self.tracker = IncidentSLATracker()
        self.telemetry = SystemHealthTelemetryCollector()
        self.pipeline = SystemHealthAuditPipeline()
        self.test_run_id = str(uuid.uuid4())

    def test_sla_compliance_evaluation_flow(self):
        # 1. Generate random incident data
        incident_id = str(uuid.uuid4())
        severity = random.choice(['critical', 'high', 'medium', 'low'])
        response_time = random.randint(10, 3600)

        # 2. Aggregate incident
        self.aggregator.register_incident(incident_id, {"severity": severity, "status": "resolved"})

        # 3. Track SLA performance
        self.tracker.record_sla_event(incident_id, {"response_time": response_time, "breached": response_time > 1800})

        # 4. Collect telemetry
        telemetry_data = {"metric_id": self.test_run_id, "value": random.random()}
        self.telemetry.collect(telemetry_data)

        # 5. Execute evaluation
        report_path = f"audit_report_{self.test_run_id}.json"
        result = self.evaluator.evaluate(
            incident_id=incident_id,
            telemetry_source=self.telemetry,
            output_path=report_path
        )

        # 6. Verify integration via audit pipeline
        pipeline_status = self.pipeline.process(report_path)

        # Assertions
        self.assertIsNotNone(result, "Evaluator failed to return compliance data")
        self.assertTrue(os.path.exists(report_path), "Audit report file was not created")
        self.assertEqual(pipeline_status['status'], 'success', "Audit pipeline failed to process the report")
        self.assertIn(self.test_run_id, str(result), "Evaluator did not incorporate telemetry data")

        # Cleanup
        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == '__main__':
    unittest.main()