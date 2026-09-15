import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.notification_template_engine import NotificationTemplateEngine

class TestNotificationTemplateEngine(unittest.TestCase):
    def setUp(self):
        self.engine = NotificationTemplateEngine()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.incident_id = f"inc-{self.random_prefix}-{random.randint(1000, 9999)}"
        self.module_name = f"mod_{uuid.uuid4().hex[:6]}"
        self.error_message = f"Error in {self.module_name}: {uuid.uuid4().hex}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_render_text_template_success(self):
        template_name = f"template_{uuid.uuid4().hex[:6]}"
        custom_msg = f"Alert message {uuid.uuid4().hex}"
        
        context = {
            "incident_id": self.incident_id,
            "module": self.module_name,
            "message": custom_msg,
            "severity": self.severity
        }

        with patch.object(self.engine, '_load_template', return_value="Incident: {incident_id} | Module: {module} | Severity: {severity} | Msg: {message}"):
            rendered = self.engine.render_text(template_name, context)
            self.assertIn(self.incident_id, rendered)
            self.assertIn(self.module_name, rendered)
            self.assertIn(custom_msg, rendered)
            self.assertIn(self.severity, rendered)

    def test_render_html_template_malformed_context(self):
        template_name = f"html_tmpl_{uuid.uuid4().hex[:6]}"
        malformed_context = {
            "error_code": random.randint(500, 599),
            "trace": uuid.uuid4().hex
        }

        with patch.object(self.engine, '_load_template', return_value="<html><body><h1>Error {error_code}</h1><p>{trace}</p></body></html>"):
            result_html = self.engine.render_html(template_name, malformed_context)
            self.assertIn(str(malformed_context["error_code"]), result_html)
            self.assertIn(malformed_context["trace"], result_html)
            self.assertTrue(result_html.startswith("<html") or "<html" in result_html.lower())

    def test_parse_stream_data_with_bytes_io(self):
        stream_content = f'{{"incident_id": "{self.incident_id}", "status": "failed", "code": {random.randint(1, 100)}}}'
        byte_stream = io.BytesIO(stream_content.encode('utf-8'))

        result = self.engine.parse_stream_data(byte_stream)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertEqual(result.get("status"), "failed")

    def test_parse_stream_data_invalid_stream(self):
        garbage_data = ''.join(random.choices(string.ascii_letters + string.punctuation, k=30))
        byte_stream = io.BytesIO(garbage_data.encode('utf-8'))

        result = self.engine.parse_stream_data(byte_stream)
        self.assertTrue(result is None or isinstance(result, dict))

    def test_generate_notification_payload_dynamic(self):
        custom_payload_key = f"key_{uuid.uuid4().hex[:4]}"
        custom_payload_val = f"val_{uuid.uuid4().hex[:4]}"
        
        raw_data = {
            custom_payload_key: custom_payload_val,
            "incident_id": self.incident_id,
            "severity": self.severity
        }

        payload = self.engine.generate_notification_payload(self.severity, self.incident_id, raw_data)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("incident_id"), self.incident_id)
        self.assertEqual(payload.get("severity"), self.severity)
        self.assertEqual(payload.get(custom_payload_key), custom_payload_val)

    def test_compile_template_with_random_syntax(self):
        dynamic_tag = f"tag_{uuid.uuid4().hex[:5]}"
        template_string = f"<div>{{% if {dynamic_tag} %}}<span>{uuid.uuid4().hex}</span>{{% endif %}}</div>"
        
        compiled = self.engine.compile_template(template_string)
        self.assertIsNotNone(compiled)