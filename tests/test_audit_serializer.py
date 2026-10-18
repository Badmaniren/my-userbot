import unittest
import json
import os
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.audit_serializer import AuditSerializer

class TestAuditSerializer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = f"/tmp/{uuid.uuid4().hex}"
        self.json_path = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.json")
        self.md_path = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.md")
        self.test_data = {
            "audit_id": uuid.uuid4().hex,
            "severity": random.choice(["CRITICAL", "WARNING", "INFO"]),
            "metrics": {f"metric_{i}": random.random() for i in range(3)}
        }
        self.serializer = AuditSerializer(self.test_data)

    def test_json_serialization_integrity(self):
        serialized = self.serializer.to_json()
        data = json.loads(serialized)
        self.assertEqual(data["audit_id"], self.test_data["audit_id"])
        self.assertEqual(data["severity"], self.test_data["severity"])

    def test_markdown_format_contains_data(self):
        md_output = self.serializer.to_markdown()
        self.assertIn(self.test_data["audit_id"], md_output)
        self.assertIn(self.test_data["severity"], md_output)

    def test_save_to_disk_json(self):
        with patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.serializer.save(self.json_path, format="json")

            mock_open.assert_called_once_with(self.json_path, 'w', encoding='utf-8')
            written_data = "".join([call.args[0] for call in mock_file.write.call_args_list])
            self.assertEqual(json.loads(written_data)["audit_id"], self.test_data["audit_id"])

    def test_save_to_disk_markdown(self):
        with patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.serializer.save(self.md_path, format="md")

            mock_open.assert_called_once_with(self.md_path, 'w', encoding='utf-8')
            mock_file.write.assert_called()
            args, _ = mock_file.write.call_args
            self.assertIn(self.test_data["audit_id"], args[0])

    def test_invalid_format_raises_error(self):
        invalid_fmt = uuid.uuid4().hex[:5]
        with self.assertRaises(ValueError):
            self.serializer.save(self.json_path, format=invalid_fmt)

    def test_telemetry_snapshot_handling(self):
        snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}
        self.test_data["telemetry"] = snapshot
        serializer = AuditSerializer(self.test_data)

        serialized = serializer.to_json()
        data = json.loads(serialized)
        self.assertEqual(data["telemetry"], snapshot)

    def test_empty_data_handling(self):
        empty_serializer = AuditSerializer({})
        result = empty_serializer.to_json()
        self.assertEqual(json.loads(result), {})

if __name__ == '__main__':
    unittest.main()