import unittest
import uuid
import random
import os
from skills.notification_template_engine import NotificationTemplateEngine
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator

class TestNotificationTemplateEngineIntegration(unittest.TestCase):
    def test_template_engine_integration_with_recovery_and_aggregator(self):
        random_suffix = str(uuid.uuid4())[:8]
        module_name = f"test_module_{random_suffix}"
        exception_msg = f"IntegrationTestException_{random_suffix}"
        exception_obj = RuntimeError(exception_msg)
        traceback_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line 1, in <module>\n    raise RuntimeError('{exception_msg}')"
        incident_id = f"inc-{uuid.uuid4()}"

        hub = ErrorRecoveryHub()
        aggregator = IncidentAggregator()
        engine = NotificationTemplateEngine()

        captured = hub.capture_failure(module_name, exception_obj, traceback_str)
        self.assertIsNotNone(captured)

        aggregated_data = aggregator.process_and_aggregate(module_name, exception_obj, traceback_str, incident_id)
        self.assertIsInstance(aggregated_data, dict)

        incident_history = hub.get_incident_history(module_name)
        self.assertIsInstance(incident_history, list)

        render_payload = {
            "incident_id": incident_id,
            "module_name": module_name,
            "error": exception_msg,
            "history_count": len(incident_history),
            "aggregated": aggregated_data
        }

        rendered_text = engine.render_template("incident_notification", render_payload, format="text")
        self.assertIn(incident_id, rendered_text)
        self.assertIn(module_name, rendered_text)

        rendered_html = engine.render_template("incident_notification", render_payload, format="html")
        self.assertIn(incident_id, rendered_html)
        self.assertIn(exception_msg, rendered_html)

        export_path = f"report_{uuid.uuid4()}.html"
        try:
            success = engine.export_notification_file(render_payload, export_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(incident_id, content)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

if __name__ == "__main__":
    unittest.main()