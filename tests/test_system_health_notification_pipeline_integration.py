import unittest
import uuid
import random
import os
from skills.system_health_notification_pipeline import SystemHealthNotificationPipeline
from skills.system_health_aggregator import SystemHealthAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher

class TestSystemHealthNotificationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.dispatcher = NotificationChannelDispatcher()
        self.pipeline = SystemHealthNotificationPipeline(
            health_aggregator=self.aggregator,
            channel_dispatcher=self.dispatcher
        )
        self.channel_name = f"test_channel_{uuid.uuid4().hex[:8]}"
        self.dispatcher.register_channel(self.channel_name, {"endpoint": "http://localhost/webhook", "active": True})

    def test_pipeline_integration_critical_alert(self):
        random_incident_id = str(uuid.uuid4())
        random_metric_value = round(random.uniform(0.0, 15.0), 2)
        random_message = f"Critical system degradation detected: error rate {random_metric_value}%"

        incidents_list = [{
            "id": random_incident_id,
            "level": "CRITICAL",
            "message": random_message,
            "metric": random_metric_value
        }]
        patches_list = []

        result = self.pipeline.process_and_notify(
            incidents_list=incidents_list,
            patches_list=patches_list,
            target_channel=self.channel_name
        )

        self.assertIsInstance(result, dict)
        self.assertIn("aggregation_result", result)
        self.assertIn("dispatch_result", result)
        self.assertTrue(result["dispatch_result"])

        broadcast_payload = {
            "level": "CRITICAL",
            "incident_id": random_incident_id,
            "message": random_message
        }
        broadcast_result = self.dispatcher.broadcast(broadcast_payload)
        self.assertIsInstance(broadcast_result, dict)
        self.assertIn(self.channel_name, broadcast_result)
        self.assertTrue(broadcast_result[self.channel_name])

if __name__ == "__main__":
    unittest.main()