import unittest
from unittest.mock import patch, mock_open
import json
import io
import uuid
import random
from datetime import datetime
from skills.dependency_audit_reporter import DependencyAuditReporter

class TestDependencyAuditReporter(unittest.TestCase):
    def setUp(self):
        self.reporter = DependencyAuditReporter()

    def test_generate_report_success(self):
        key = uuid.uuid4().hex
        value = uuid.uuid4().hex
        audit_data = {key: value}
        
        result_json = self.reporter.generate_report(audit_data)
        parsed = json.loads(result_json)
        
        self.assertEqual(parsed[key], value)
        self.assertIn("timestamp", parsed)

    def test_generate_report_error(self):
        err_code = random.randint(1000, 9999)
        audit_data = {"error_code": err_code}
        
        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            result = self.reporter.generate_report(audit_data)
            
        self.assertIn(f"ERROR: code {err_code}", result)
        self.assertIn(f"ERROR: code {err_code}", mock_stderr.getvalue())

    def test_generate_report_string_input(self):
        str_input = f"audit_str_{uuid.uuid4().hex}"
        result_json = self.reporter.generate_report(str_input)
        parsed = json.loads(result_json)
        self.assertEqual(parsed["data"], str_input)
        self.assertIn("timestamp", parsed)

    def test_finalize_epic(self):
        epic_id = uuid.uuid4().hex
        raw_data = uuid.uuid4().bytes
        stream = io.BytesIO(raw_data)
        expected_filename = f"epic_{epic_id}_audit.log"
        
        m_open = mock_open()
        with patch("builtins.open", m_open):
            success = self.reporter.finalize_epic(epic_id, stream)
            
        self.assertTrue(success)
        m_open.assert_called_once_with(expected_filename, "wb")
        m_open().write.assert_called_once_with(raw_data)

    def test_export_summary(self):
        payload_key = uuid.uuid4().hex
        payload_val = uuid.uuid4().hex
        payload = {payload_key: payload_val}
        
        exported = self.reporter.export_summary(payload, format="json")
        parsed = json.loads(exported)
        
        self.assertEqual(parsed[payload_key], payload_val)

    def test_generate_epic_report(self):
        payload_key = uuid.uuid4().hex
        payload_val = uuid.uuid4().hex
        payload = {payload_key: payload_val}
        output_path = f"{uuid.uuid4().hex}.json"
        
        m_open = mock_open()
        with patch("builtins.open", m_open):
            success = self.reporter.generate_epic_report(payload, output_path)
            
        self.assertTrue(success)
        m_open.assert_called_once_with(output_path, "w", encoding="utf-8")
        written_data = "".join(call.args[0] for call in m_open().write.call_args_list)
        parsed_written = json.loads(written_data)
        self.assertEqual(parsed_written[payload_key], payload_val)

if __name__ == "__main__":
    unittest.main()