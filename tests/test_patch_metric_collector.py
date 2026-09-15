import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
import json
import os

from skills.patch_metric_collector import start_new, PatchMetricCollector


class TestPatchMetricCollectorArchitect(unittest.TestCase):

    def setUp(self):
        self.collector = PatchMetricCollector()
        self.random_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_incident = str(uuid.uuid4())
        self.random_error = f"error_{uuid.uuid4().hex[:6]}"
        self.random_output = f"metrics_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.random_output):
            try:
                os.remove(self.random_output)
            except OSError:
                pass

    def test_start_new_success_execution(self):
        custom_patch = {uuid.uuid4().hex: uuid.uuid4().hex}
        raw_stream = io.BytesIO("".join(random.choices(string.ascii_letters, k=32)).encode('utf-8'))
        
        with patch('random.randint', return_value=random.randint(1, 50)):
            result = start_new(
                success=True,
                incident_id=self.random_incident,
                error=None,
                raw_result=raw_stream,
                patch_data=custom_patch
            )

        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, self.random_incident)
        self.assertIsNone(result.error)
        self.assertEqual(result.raw_result, raw_stream)
        self.assertEqual(result.patch_data, custom_patch)

    def test_start_new_failure_execution(self):
        # Исправлено: генерация байтов с использованием encode() вместо несуществующего ascii_bytes
        random_bytes_list = random.choices(string.ascii_lowercase.encode('utf-8') if hasattr(string, 'ascii_bytes') else b'abcdef', k=32)
        stream_data = io.BytesIO(b"".join(bytes([b]) for b in random_bytes_list))
        
        with patch('random.randint', return_value=random.randint(51, 100)):
            result = start_new(
                success=False,
                incident_id=self.random_incident,
                error=self.random_error,
                raw_result=stream_data,
                patch_data=None
            )

        self.assertFalse(result.success)
        self.assertEqual(result.incident_id, self.random_incident)
        self.assertEqual(result.error, self.random_error)
        self.assertIsInstance(result.patch_data, dict)
        self.assertEqual(len(result.patch_data), 0)

    def test_record_metric_and_summary(self):
        payload = {
            "module": self.random_module,
            "incident": self.random_incident,
            "score": random.random()
        }
        
        recorded = self.collector.record_metric(payload)
        self.assertEqual(recorded, payload)
        self.assertIn(payload, self.collector.metrics)

        summary = self.collector.get_metrics_summary(module_name=self.random_module)
        parsed = json.loads(summary)
        
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["incident"], self.random_incident)
        self.assertEqual(parsed[0]["module"], self.random_module)

    def test_export_metrics_json(self):
        payload = {
            "id": uuid.uuid4().hex,
            "status": random.choice(["success", "failed"])
        }
        self.collector.record_metric(payload)

        success_export = self.collector.export_metrics(self.random_output, format="json")
        self.assertTrue(success_export)
        self.assertTrue(os.path.exists(self.random_output))

        with open(self.random_output, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], payload["id"])
        self.assertEqual(data[0]["status"], payload["status"])

    def test_export_metrics_unsupported_format(self):
        payload = {"data": uuid.uuid4().hex}
        self.collector.record_metric(payload)

        bad_format = uuid.uuid4().hex[:4]
        success_export = self.collector.export_metrics(self.random_output, format=bad_format)
        self.assertFalse(success_export)
        self.assertFalse(os.path.exists(self.random_output))