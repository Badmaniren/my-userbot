import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.patch_metric_collector import start_new


class TestPatchMetricCollectorArchitect(unittest.TestCase):

    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.module_name = "".join(random.choices(string.ascii_lowercase, k=10))
        self.error_message = "".join(random.choices(string.ascii_letters, k=20))
        self.random_score = random.uniform(0.0, 100.0)

    def test_start_new_success_execution(self):
        dynamic_success = True
        dynamic_patch_data = {
            "".join(random.choices(string.ascii_lowercase, k=5)): str(uuid.uuid4())
        }
        
        with patch("skills.patch_metric_collector.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = self.incident_id
            
            result = start_new(
                success=dynamic_success,
                incident_id=self.incident_id,
                patch_data=dynamic_patch_data
            )
            
            self.assertIsNotNone(result)
            self.assertTrue(getattr(result, "success", True))
            self.assertEqual(getattr(result, "incident_id", None), self.incident_id)
            self.assertEqual(getattr(result, "patch_data", {}), dynamic_patch_data)

    def test_start_new_failure_execution(self):
        dynamic_success = False
        dynamic_error = "".join(random.choices(string.printable, k=15))
        stream_data = io.BytesIO(b"".join(random.choices(string.ascii_bytes if hasattr(string, 'ascii_bytes') else b'abcdef', k=32)))
        
        with patch("skills.patch_metric_collector.random.randint") as mock_rand:
            mock_rand.return_value = 42
            
            result = start_new(
                success=dynamic_success,
                incident_id=self.incident_id,
                error=dynamic_error,
                raw_result=stream_data
            )
            
            self.assertIsNotNone(result)
            self.assertFalse(getattr(result, "success", True))
            self.assertEqual(getattr(result, "error", None), dynamic_error)

    def test_start_new_metric_collection_chaos(self):
        metric_key = "".join(random.choices(string.ascii_uppercase, k=8))
        metric_val = random.randint(100, 999)
        
        payload = {
            metric_key: metric_val,
            "module": self.module_name,
            "score": self.random_score
        }
        
        with patch("skills.patch_metric_collector.PipelineResult") as mock_pipeline:
            mock_instance = MagicMock()
            mock_instance.success = True
            mock_instance.incident_id = self.incident_id
            mock_instance.patch_data = payload
            mock_pipeline.return_value = mock_instance
            
            res = start_new(
                success=True,
                incident_id=self.incident_id,
                patch_data=payload
            )
            
            self.assertTrue(res.success)
            self.assertEqual(res.incident_id, self.incident_id)
            self.assertIn(metric_key, res.patch_data)
            self.assertEqual(res.patch_data[metric_key], metric_val)


if __name__ == "__main__":
    unittest.main()