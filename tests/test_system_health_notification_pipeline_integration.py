import unittest
import uuid
import random
from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.system_health_notification_pipeline import SystemHealthNotificationPipeline

class TestSystemHealthNotificationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.dispatcher = NotificationChannelDispatcher()
        self.pipeline = SystemHealthNotificationPipeline(
            health_aggregator=self.aggregator,
            channel_dispatcher=self.dispatcher
        )
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.channel_config = {"active": True, "endpoint": f"https://example.com/webhook/{uuid.uuid4().hex}"}
        self.pipeline.register_alert_channel(self.channel_name, self.channel_config)

    def test_custom_alert_dispatch_integration(self):
        incident_id = str(uuid.uuid4())
        level = random.choice(["INFO", "WARNING", "CRITICAL"])
        message = f"Random system check alert message: {uuid.uuid4().hex}"
        
        payload = self.dispatcher.format_payload(level, incident_id, message)
        dispatch_result = self.pipeline.send_custom_alert(self.channel_name, payload)
        
        self.assertIsInstance(dispatch_result, bool)
        self.assertTrue(dispatch_result)

    def test_process_and_notify_integration(self):
        random_id = str(uuid.uuid4())
        random_level = random.choice(["CRITICAL", "ERROR"])
        random_message = f"Integration test failure message {uuid.uuid4().hex}"
        
        incidents_list = [{
            "id": random_id,
            "level": random_level,
            "message": random_message
        }]
        patches_list = []
        
        result = self.pipeline.process_and_notify(incidents_list, patches_list, self.channel_name)
        
        self.assertIn("aggregation_result", result)
        self.assertIn("dispatch_result", result)
        self.assertTrue(result["dispatch_result"])

    def test_stream_processing_and_dispatch_integration(self):
        stream_data = f'{{"level": "CRITICAL", "incident_id": "{uuid.uuid4()}", "message": "Stream alert {uuid.uuid4().hex}"}}'
        temp_path = f"test_stream_{uuid.uuid4().hex}.json"
        
        try:
            broadcast_result = self.pipeline.process_stream_and_dispatch(stream_data, temp_path)
            self.assertIsInstance(broadcast_result, dict)
            self.assertIn(self.channel_name, broadcast_result)
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()