import unittest
import uuid
import random
import os
import json
from skills.incident_sla_compliance_reporter import incident_sla_compliance_reporter, IncidentSlaComplianceReporter, ComplianceReportError
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner

class TestIncidentSlaComplianceReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.metric_id = str(uuid.uuid4())
        self.score = random.randint(50, 100)

        # Получаем реальные данные от связанных навыков (без моков)
        self.tracker_metrics = incident_sla_tracker(self.incident_id, {"metric_id": self.metric_id, "score": self.score})
        self.breach_predictors = incident_sla_breach_predictor(self.incident_id, self.tracker_metrics)
        self.mitigation_plans = incident_sla_mitigation_planner(self.incident_id, self.breach_predictors)

    def tearDown(self):
        report_file_path = f"audit_report_{self.incident_id}.log"
        if os.path.exists(report_file_path):
            os.remove(report_file_path)

    def test_compliance_reporter_integration_flow(self):
        report = incident_sla_compliance_reporter(
            incident_id=self.incident_id,
            tracker_metrics=self.tracker_metrics,
            breach_predictors=self.breach_predictors,
            mitigation_plans=self.mitigation_plans
        )

        self.assertIsInstance(report, dict)
        self.assertEqual(report["reporter_id"], self.incident_id)
        self.assertEqual(report["metrics"]["metric_id"], self.metric_id)
        self.assertIn("predictors", report)
        self.assertIn("mitigation_plans", report)

        report_file_path = f"audit_report_{self.incident_id}.log"
        self.assertTrue(os.path.exists(report_file_path))

        with open(report_file_path, "r") as f:
            lines = f.readlines()
            self.assertTrue(any(self.incident_id in line for line in lines))

    def test_compliance_reporter_class_methods(self):
        reporter = IncidentSlaComplianceReporter(reporter_id=self.incident_id, standard="ISO-27001")

        audit_report = reporter.generate_audit_report(
            tracker_metrics=self.tracker_metrics,
            breach_predictors=self.breach_predictors,
            mitigation_plans=self.mitigation_plans
        )
        self.assertEqual(audit_report["standard"], "ISO-27001")

        status_log = reporter.create_compliance_status_log({
            "log_prefix": f"prefix_{random.randint(1, 100)}",
            "audit_passed": True,
            "score": self.score
        })
        self.assertIn(self.incident_id, reporter.reporter_id)
        self.assertIn("Standard: ISO-27001", status_log)
        self.assertIn(f"Score: {self.score}", status_log)

    def test_generate_audit_report_invalid_metrics(self):
        reporter = IncidentSlaComplianceReporter(reporter_id=self.incident_id, standard="ISO-9001")
        with self.assertRaises(ComplianceReportError):
            reporter.generate_audit_report(
                tracker_metrics={"invalid": "data"},
                breach_predictors=self.breach_predictors,
                mitigation_plans=self.mitigation_plans
            )

if __name__ == "__main__":
    unittest.main()