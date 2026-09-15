import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.notification_channel_dispatcher import NotificationChannelDispatcher

class TestNotificationChannelDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = NotificationChannelDispatcher()
        self.random_channel = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident = uuid.uuid4().hex
        self.random_message = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        self.random_url = f"https://{uuid.uuid4().hex}.com/webhook"

    def test_init_channels(self):
        self.assertIsInstance(self.dispatcher.channels, dict)

    def test_register_channel(self):
        config = {
            "url": self.random_url,
            "token": uuid.uuid4().hex
        }
        self.dispatcher.register_channel(self.random_channel, config)
        self.assertIn(self.random_channel, self.dispatcher.channels)
        self.assertEqual(self.dispatcher.channels[self.random_channel]["url"], self.random_url)

    def test_dispatch_critical_failure_success(self):
        config = {
            "url": self.random_url,
            "type": "webhook"
        }
        self.dispatcher.register_channel(self.random_channel, config)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            payload = {
                "incident_id": self.random_incident,
                "message": self.random_message
            }
            
            result = self.dispatcher.dispatch(self.random_channel, payload)
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertEqual(called_url, self.random_url)

    def test_dispatch_critical_failure_http_error(self):
        config = {
            "url": self.random_url,
            "type": "webhook"
        }
        self.dispatcher.register_channel(self.random_channel, config)

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            payload = {
                "incident_id": self.random_incident,
                "message": self.random_message
            }
            
            result = self.dispatcher.dispatch(self.random_channel, payload)
            
            self.assertFalse(result)

    def test_dispatch_stdout_success(self):
        config = {
            "type": "stdout",
            "active": True
        }
        self.dispatcher.register_channel(self.random_channel, config)
        payload = {
            "incident_id": self.random_incident,
            "message": self.random_message
        }
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = self.dispatcher.dispatch(self.random_channel, payload)
            self.assertTrue(result)
            self.assertIn(self.random_incident, mock_stdout.getvalue())

    def test_dispatch_inactive_channel(self):
        config = {
            "type": "stdout",
            "active": False
        }
        self.dispatcher.register_channel(self.random_channel, config)
        payload = {
            "incident_id": self.random_incident,
            "message": self.random_message
        }
        result = self.dispatcher.dispatch(self.random_channel, payload)
        self.assertFalse(result)

    def test_dispatch_unknown_channel(self):
        unknown_chan = uuid.uuid4().hex
        payload = {
            "incident_id": self.random_incident,
            "message": self.random_message
        }
        result = self.dispatcher.dispatch(unknown_chan, payload)
        self.assertFalse(result)

    def test_broadcast_recovery_status(self):
        chan_1 = uuid.uuid4().hex
        chan_2 = uuid.uuid4().hex
        
        self.dispatcher.register_channel(chan_1, {"url": f"https://{uuid.uuid4().hex}.com"})
        self.dispatcher.register_channel(chan_2, {"url": f"https://{uuid.uuid4().hex}.com"})

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            recovery_payload = {
                "status": "RECOVERED",
                "incident_id": self.random_incident,
                "module": ''.join(random.choices(string.ascii_lowercase, k=8))
            }

            results = self.dispatcher.broadcast(recovery_payload)
            
            self.assertIn(chan_1, results)
            self.assertIn(chan_2, results)
            self.assertTrue(results[chan_1])
            self.assertTrue(results[chan_2])
            self.assertEqual(mock_post.call_count, 2)

    def test_parse_stream_data_valid(self):
        stream_content = json.dumps({
            "channel": self.random_channel,
            "incident_id": self.random_incident,
            "payload": {
                "error": self.random_message
            }
        }).encode('utf-8')
        
        stream = io.BytesIO(stream_content)
        parsed = self.dispatcher.parse_stream_data(stream)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["incident_id"], self.random_incident)
        self.assertEqual(parsed["channel"], self.random_channel)

    def test_parse_stream_data_invalid(self):
        stream_content = b"INVALID_STREAM_CORRUPTED_DATA_" + uuid.uuid4().bytes
        stream = io.BytesIO(stream_content)
        parsed = self.dispatcher.parse_stream_data(stream)
        self.assertIsNone(parsed)

    def test_format_notification_payload(self):
        level = random.choice(["CRITICAL", "WARNING", "INFO"])
        formatted = self.dispatcher.format_payload(level, self.random_incident, self.random_message)
        
        self.assertIn(level, formatted.values() if isinstance(formatted, dict) else str(formatted))
        self.assertIn(self.random_incident, str(formatted))
        self.assertIn(self.random_message, str(formatted))