import unittest
from unittest.mock import patch, MagicMock
import json
import io
import random
import uuid
import string

from skills.notification_template_engine import NotificationTemplateEngine

class TestNotificationTemplateEngine(unittest.TestCase):

    def setUp(self):
        self.engine = NotificationTemplateEngine()
        self.random_incident_id = uuid.uuid4().hex
        self.random_error_msg = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        self.random_level = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        self.random_channel = f"channel_{uuid.uuid4().hex[:8]}"

    def test_render_dict_payload(self):
        payload = {
            "id": self.random_incident_id,
            "error": self.random_error_msg,
            "level": self.random_level
        }
        rendered = self.engine.render(payload)
        parsed = json.loads(rendered)
        self.assertEqual(parsed.get("id"), self.random_incident_id)
        self.assertEqual(parsed.get("error"), self.random_error_msg)
        self.assertEqual(parsed.get("level"), self.random_level)

    def test_render_string_payload(self):
        raw_string = f"System failure: {self.random_error_msg} [{self.random_incident_id}]"
        rendered = self.engine.render(raw_string)
        self.assertEqual(rendered, raw_string)

    def test_render_template(self):
        template_name = f"tpl_{uuid.uuid4().hex[:6]}"
        context = {
            "incident_id": self.random_incident_id,
            "error": self.random_error_msg
        }
        rendered = self.engine.render_template(template_name, context)
        self.assertIn(template_name, rendered)
        self.assertIn(self.random_incident_id, rendered)
        self.assertIn(self.random_error_msg, rendered)

    def test_format_payload(self):
        formatted = self.engine.format_payload(
            level=self.random_level,
            incident_id=self.random_incident_id,
            message=self.random_error_msg
        )
        self.assertIsInstance(formatted, dict)
        self.assertEqual(formatted.get("level"), self.random_level)
        self.assertEqual(formatted.get("incident_id"), self.random_incident_id)
        self.assertEqual(formatted.get("message"), self.random_error_msg)

    def test_parse_stream_data_with_bytes_stream(self):
        random_bytes = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        parsed = self.engine.parse_stream_data(stream)
        self.assertEqual(parsed, random_bytes)

    def test_parse_stream_data_invalid_stream(self):
        non_stream_object = {"data": uuid.uuid4().hex}
        parsed = self.engine.parse_stream_data(non_stream_object)
        self.assertIsNone(parsed)

    def test_send_templated_success(self):
        payload = {
            "id": self.random_incident_id,
            "msg": self.random_error_msg,
            "severity": self.random_level
        }
        with patch.object(self.engine.dispatcher, 'dispatch', return_value=True) as mock_dispatch:
            success = self.engine.send_templated(self.random_channel, payload)
            self.assertTrue(success)
            mock_dispatch.assert_called_once()
            args = mock_dispatch.call_args[0]
            self.assertEqual(args[0], self.random_channel)
            self.assertEqual(args[1]["incident_id"], self.random_incident_id)
            self.assertEqual(args[1]["message"], self.random_error_msg)
            self.assertEqual(args[1]["level"], self.random_level)

    def test_broadcast_template(self):
        payload = {
            "epic_id": self.random_incident_id,
            "details": self.random_error_msg,
            "level": self.random_level
        }
        expected_results = {
            self.random_channel: True,
            f"backup_{uuid.uuid4().hex[:4]}": True
        }
        with patch.object(self.engine.dispatcher, 'broadcast', return_value=expected_results) as mock_broadcast:
            results = self.engine.broadcast_template(payload)
            self.assertEqual(results, expected_results)
            mock_broadcast.assert_called_once()
            formatted_arg = mock_broadcast.call_args[0][0]
            self.assertEqual(formatted_arg["incident_id"], self.random_incident_id)
            self.assertEqual(formatted_arg["message"], self.random_error_msg)
            self.assertEqual(formatted_arg["level"], self.random_level)

    def test_send_templated_robust_fallback_when_fails(self):
        payload = {
            "incident_id": self.random_incident_id,
            "message": self.random_error_msg,
            "level": self.random_level
        }
        with patch.object(self.engine.dispatcher, 'dispatch', return_value=False) as mock_dispatch:
            success = self.engine.send_templated(self.random_channel, payload)
            self.assertFalse(success)
            mock_dispatch.assert_called_once()