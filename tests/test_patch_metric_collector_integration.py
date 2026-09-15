import unittest
import os
import uuid
import random
import json
from skills.patch_metric_collector import PatchMetricCollector, start_new
from skills.auto_patch_pipeline import PipelineResult


class TestPatchMetricCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.collector = PatchMetricCollector()
        self.test_output_path = f"test_metrics_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.test_output_path):
            try:
                os.remove(self.test_output_path)
            except OSError:
                pass

    def test_integration_metric_pipeline_workflow(self):
        random_success = random.choice([True, False])
        random_incident_id = str(uuid.uuid4())
        random_error_code = f"ERR_CODE_{random.randint(100, 999)}"
        random_module = f"module_{uuid.uuid4().hex[:6]}"

        pipeline_res = start_new(
            success=random_success,
            incident_id=random_incident_id,
            error=random_error_code,
            raw_result={"output": "executed"},
            patch_data={"patch_version": random.randint(1, 5)}
        )

        self.assertIsInstance(pipeline_res, PipelineResult)
        self.assertEqual(pipeline_res.incident_id, random_incident_id)
        self.assertEqual(pipeline_res.success, random_success)
        self.assertEqual(pipeline_res.error, random_error_code)

        metric_payload = {
            "module": random_module,
            "incident_id": pipeline_res.incident_id,
            "success": pipeline_res.success,
            "error": pipeline_res.error,
            "patch_info": pipeline_res.patch_data
        }

        recorded = self.collector.record_metric(metric_payload)
        self.assertEqual(recorded["incident_id"], random_incident_id)
        self.assertEqual(recorded["module"], random_module)

        summary_json = self.collector.get_metrics_summary(module_name=random_module)
        parsed_summary = json.loads(summary_json)
        
        self.assertTrue(any(m["incident_id"] == random_incident_id for m in parsed_summary))

        export_success = self.collector.export_metrics(self.test_output_path, format="json")
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(self.test_output_path))

        with open(self.test_output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertGreaterEqual(len(file_data), 1)
        found = False
        for item in file_data:
            if item.get("incident_id") == random_incident_id:
                found = True
                self.assertEqual(item.get("error"), random_error_code)
                self.assertEqual(item.get("success"), random_success)
        self.assertTrue(found, "Экспортированные метрики должны содержать созданный случайный инцидент")


if __name__ == "__main__":
    unittest.main()