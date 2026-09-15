import unittest
import uuid
import random
import os
import tempfile
from skills.patch_metric_collector import PatchMetricCollector
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_scheduler import PatchScheduler
from skills.auto_patch_pipeline import PipelineResult

class TestPatchMetricCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = PatchMetricCollector()
        self.recovery_hub = ErrorRecoveryHub()
        self.scheduler = PatchScheduler()
        self.incident_id = str(uuid.uuid4())
        self.module_name = f"test_module_{random.randint(1000, 9999)}"
        self.error_message = f"Simulated error {uuid.uuid4()}"

    def test_end_to_end_metric_collection_and_pipeline(self):
        try:
            raise RuntimeError(self.error_message)
        except RuntimeError as e:
            incident_data = self.recovery_hub.capture_failure(
                self.module_name, e, "Traceback info..."
            )
            
        patch_payload = {
            "incident_id": self.incident_id,
            "patch_code": "print('fixed')",
            "module": self.module_name
        }
        
        scheduled = self.scheduler.coordinate_and_schedule(
            self.incident_id, patch_payload, self.recovery_hub
        )
        
        pipeline_res = PipelineResult(
            success=True,
            incident_id=self.incident_id,
            error=None,
            raw_result="Applied successfully",
            patch_data=patch_payload
        )
        
        metrics_payload = {
            "incident_id": self.incident_id,
            "module": self.module_name,
            "pipeline_result": pipeline_res,
            "success": pipeline_res.success
        }
        
        collected_metrics = self.collector.record_metric(metrics_payload)
        self.assertIsNotNone(collected_metrics)
        
        summary = self.collector.get_metrics_summary(self.module_name)
        self.assertIn(self.incident_id, str(summary))

    def test_metric_export_creates_actual_file(self):
        temp_dir = tempfile.gettempdir()
        output_filename = f"metrics_{uuid.uuid4()}.json"
        output_path = os.path.join(temp_dir, output_filename)
        
        random_success = random.choice([True, False])
        pipeline_res = PipelineResult(
            success=random_success,
            incident_id=self.incident_id,
            error="None" if random_success else "Timeout",
            raw_result="Raw data",
            patch_data={"id": self.incident_id}
        )
        
        self.collector.record_metric({
            "incident_id": self.incident_id,
            "pipeline_result": pipeline_res,
            "success": random_success
        })
        
        export_result = self.collector.export_metrics(output_path, format="json")
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)
            
        os.remove(output_path)

if __name__ == "__main__":
    unittest.main()