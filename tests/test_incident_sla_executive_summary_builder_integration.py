import unittest
import os
import uuid
import random
import json
from skills.incident_sla_executive_summary_builder import (
    IncidentSlaExecutiveSummaryBuilder,
    incident_sla_executive_summary_builder
)
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_auto_recovery_dispatcher import incident_auto_recovery_dispatcher
from skills.incident_business_loss_reporter import incident_business_loss_reporter

class TestIncidentSlaExecutiveSummaryBuilderIntegration(unittest.TestCase):
    def test_executive_summary_pipeline_integration(self):
        rand_suffix = uuid.uuid4().hex[:8]
        incident_id = f"INC-{random.randint(10000, 99999)}-{rand_suffix}"
        output_path = f"./test_output/summary_{rand_suffix}.json"

        mock_sla_input = {
            "sla_status": "breached",
            "delay_minutes": random.randint(15, 120)
        }
        mock_recovery_input = {
            "dispatcher_status": "success",
            "attempts": random.randint(1, 5)
        }
        mock_business_input = {
            "estimated_loss_usd": float(random.randint(1000, 50000)),
            "affected_users": random.randint(100, 10000)
        }

        builder_class_instance = IncidentSlaExecutiveSummaryBuilder()
        built_summary = builder_class_instance.build_summary(incident_id)

        self.assertIn("sla_summary", built_summary)
        self.assertIn("recovery_summary", built_summary)
        self.assertIn("business_impact", built_summary)

        export_result = builder_class_instance.export_summary(incident_id, "json")
        self.assertEqual(export_result["export_status"], "success")
        self.assertEqual(export_result["format"], "json")

        stream_data = builder_class_instance.process_summary_stream(rand_suffix)
        self.assertIsInstance(stream_data, bytes)

        func_result = incident_sla_executive_summary_builder(
            incident_id=incident_id,
            sla_data=mock_sla_input,
            recovery_data=mock_recovery_input,
            business_loss_data=mock_business_input,
            output_path=output_path
        )

        self.assertEqual(func_result["incident_id"], incident_id)
        self.assertEqual(func_result["sla_data"], mock_sla_input)
        self.assertEqual(func_result["recovery_data"], mock_recovery_input)
        self.assertEqual(func_result["business_loss_data"], mock_business_input)

        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)
            self.assertEqual(file_content["summary_id"], incident_id)
            self.assertEqual(file_content["business_loss_data"]["affected_users"], mock_business_input["affected_users"])

        if os.path.exists(output_path):
            os.remove(output_path)
        dir_name = os.path.dirname(output_path)
        if dir_name and os.path.exists(dir_name):
            try:
                os.rmdir(dir_name)
            except OSError:
                pass

if __name__ == "__main__":
    unittest.main()