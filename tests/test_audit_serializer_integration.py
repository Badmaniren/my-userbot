import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.audit_serializer import AuditSerializer


class TestAuditSerializerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_audit_ser_")
        self.log_path = os.path.join(self.test_dir, f"anomaly_{uuid.uuid4().hex}.log")
        self.json_path = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.json")
        self.md_path = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.md")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_serialize_and_save_json_pipeline(self):
        logger = AnomalyLogger(self.log_path)
        serializer = AuditSerializer()

        random_source = f"sensor_{uuid.uuid4().hex[:8]}"
        random_token = f"token_{uuid.uuid4().hex}"
        random_cpu = round(random.uniform(50.0, 99.9), 2)
        random_details = {"incident_id": random_token, "error_code": random.randint(100, 999)}
        random_telemetry = {"cpu_usage": random_cpu, "memory_mb": random.randint(1024, 8192)}

        logger.log_anomaly(
            source=random_source,
            severity="critical",
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        structured_report = logger.get_structured_report()
        self.assertIsInstance(structured_report, (dict, list))

        json_str = serializer.serialize_json(structured_report)
        self.assertIsInstance(json_str, str)
        self.assertIn(random_token, json_str)
        self.assertIn(random_source, json_str)

        deserialized = json.loads(json_str)
        self.assertIsInstance(deserialized, (dict, list))

        result_path = serializer.save_json(structured_report, self.json_path)
        self.assertTrue(os.path.exists(self.json_path))
        if result_path is not None:
            self.assertEqual(os.path.abspath(result_path), os.path.abspath(self.json_path))

        with open(self.json_path, "r", encoding="utf-8") as f:
            disk_data = json.load(f)

        self.assertIn(random_token, json.dumps(disk_data))
        self.assertIn(random_source, json.dumps(disk_data))

    def test_serialize_and_save_markdown_pipeline(self):
        logger = AnomalyLogger(self.log_path)
        serializer = AuditSerializer()

        items_count = random.randint(2, 4)
        generated_tokens = []

        for i in range(items_count):
            token = f"audit_entry_{uuid.uuid4().hex}"
            generated_tokens.append(token)
            logger.log_anomaly(
                source=f"service_{uuid.uuid4().hex[:6]}",
                severity="high" if i % 2 == 0 else "medium",
                details={"desc": token, "index": i},
                telemetry_snapshot={"metric_val": random.uniform(1.0, 100.0)}
            )

        structured_report = logger.get_structured_report()

        md_str = serializer.serialize_markdown(structured_report)
        self.assertIsInstance(md_str, str)
        self.assertGreater(len(md_str), 0)

        for token in generated_tokens:
            self.assertIn(token, md_str)

        result_path = serializer.save_markdown(structured_report, self.md_path)
        self.assertTrue(os.path.exists(self.md_path))
        if result_path is not None:
            self.assertEqual(os.path.abspath(result_path), os.path.abspath(self.md_path))

        with open(self.md_path, "r", encoding="utf-8") as f:
            disk_md_content = f.read()

        for token in generated_tokens:
            self.assertIn(token, disk_md_content)

    def test_export_empty_and_custom_reports(self):
        serializer = AuditSerializer()
        custom_audit_id = f"custom_audit_{uuid.uuid4().hex}"
        custom_payload = {
            "audit_id": custom_audit_id,
            "status": "passed",
            "findings": [],
            "metrics": {"duration_ms": random.randint(10, 500)}
        }

        json_out = serializer.serialize_json(custom_payload)
        parsed = json.loads(json_out)
        self.assertEqual(parsed.get("audit_id"), custom_audit_id)

        md_out = serializer.serialize_markdown(custom_payload)
        self.assertIn(custom_audit_id, md_out)

        sub_dir = os.path.join(self.test_dir, f"nested_{uuid.uuid4().hex[:6]}")
        nested_json_path = os.path.join(sub_dir, "nested_report.json")

        serializer.save_json(custom_payload, nested_json_path)
        self.assertTrue(os.path.exists(nested_json_path))
        with open(nested_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("audit_id"), custom_audit_id)


if __name__ == "__main__":
    unittest.main()