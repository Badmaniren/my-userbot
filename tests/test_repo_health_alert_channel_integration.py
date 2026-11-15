import unittest
import uuid
import random
import os
from skills.repo_health_alert_channel import RepoHealthAlertChannel
from skills.repo_health_collector import RepoHealthCollector
from skills.repo_health_dispatcher import RepoHealthDispatcher
from skills.repo_logger import RepoLogger

class TestRepoHealthAlertChannelIntegration(unittest.TestCase):
    def test_alert_channel_end_to_end_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        metric_value = round(random.uniform(0.0, 50.0), 2)
        
        collector = RepoHealthCollector()
        dispatcher = RepoHealthDispatcher()
        logger = RepoLogger()
        alert_channel = RepoHealthAlertChannel()

        collected_data = collector.collect(repo_id=unique_repo_id, health_score=metric_value)
        self.assertIsNotNone(collected_data)

        dispatched_event = dispatcher.dispatch(payload=collected_data)
        self.assertIsNotNone(dispatched_event)

        logged_action = logger.log_event(event_id=str(uuid.uuid4()), data=dispatched_event)
        self.assertIsNotNone(logged_action)

        alert_result = alert_channel.send_alert(
            channel_id=str(uuid.uuid4()),
            alert_payload={
                "repo": unique_repo_id,
                "score": metric_value,
                "status": "CRITICAL",
                "log_ref": logged_action
            }
        )

        self.assertIn("status", alert_result)
        self.assertEqual(alert_result["status"], "SENT")
        self.assertEqual(alert_result["repo"], unique_repo_id)

if __name__ == "__main__":
    unittest.main()