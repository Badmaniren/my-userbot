import unittest
from unittest.mock import patch
import os
import json
import io
import uuid
import random

from skills.incident_sla_executive_summary_builder import (
    IncidentSlaExecutiveSummaryBuilder,
    incident_sla_executive_summary_builder
)

class TestIncidentSlaExecutiveSummaryBuilder(unittest.TestCase):

    def test_build_summary_logic(self):
        summary_id = uuid.uuid4().hex
        builder = IncidentSlaExecutiveSummaryBuilder()

        expected_sla = {"breached": random.choice([True, False]), "margin_sec": random.randint(10, 500)}
        expected_recovery = {"status": random.choice(["success", "failed"]), "steps": random.randint(1, 5)}
        expected_business = {"loss_usd": random.uniform(100.0, 9999.0), "tier": random.choice(["P1", "P2", "P3"])}

        with patch.object(builder, '_fetch_sla_data', return_value=expected_sla) as mock_sla, \
             patch.object(builder, '_fetch_recovery_data', return_value=expected_recovery) as mock_rec, \
             patch.object(builder, '_fetch_business_metrics', return_value=expected_business) as mock_bus:

            result = builder.build_summary(summary_id)

            mock_sla.assert_called_once_with(summary_id)
            mock_rec.assert_called_once_with(summary_id)
            mock_bus.assert_called_once_with(summary_id)

            self.assertEqual(result["sla_summary"], expected_sla)
            self.assertEqual(result["recovery_summary"], expected_recovery)
            self.assertEqual(result["business_impact"], expected_business)

    def test_process_summary_stream(self):
        stream_id = uuid.uuid4().hex
        random_bytes = uuid.uuid4().bytes
        builder = IncidentSlaExecutiveSummaryBuilder()

        with patch.object(builder, '_get_raw_stream', return_value=io.BytesIO(random_bytes)) as mock_stream:
            result = builder.process_summary_stream(stream_id)
            mock_stream.assert_called_once_with(stream_id)
            self.assertEqual(result, random_bytes)

    def test_export_summary(self):
        export_token = uuid.uuid4().hex
        format_type = random.choice(["json", "pdf", "xml", "html"])
        builder = IncidentSlaExecutiveSummaryBuilder()

        mock_summary = {
            "sla_summary": {"id": uuid.uuid4().hex},
            "recovery_summary": {"id": uuid.uuid4().hex},
            "business_impact": {"id": uuid.uuid4().hex}
        }

        with patch.object(builder, 'build_summary', return_value=mock_summary) as mock_build:
            result = builder.export_summary(export_token, format_type)
            mock_build.assert_called_once_with(export_token)

            self.assertEqual(result["export_status"], "success")
            self.assertEqual(result["format"], format_type)
            self.assertEqual(result["data"], mock_summary)

class TestIncidentSlaExecutiveSummaryBuilderIntegration(unittest.TestCase):

    def test_functional_summary_builder_file_output(self):
        incident_id = uuid.uuid4().hex
        sla_data = {"metric": uuid.uuid4().hex, "value": random.randint(1, 100)}
        recovery_data = {"status": uuid.uuid4().hex, "duration": random.randint(5, 50)}
        business_loss_data = {"loss": round(random.uniform(10.0, 5000.0), 2)}

        output_path = os.path.join("temp_outputs", f"{uuid.uuid4().hex}.json")

        try:
            result = incident_sla_executive_summary_builder(
                incident_id=incident_id,
                sla_data=sla_data,
                recovery_data=recovery_data,
                business_loss_data=business_loss_data,
                output_path=output_path
            )

            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["summary_id"], incident_id)
            self.assertEqual(result["sla_data"], sla_data)
            self.assertEqual(result["recovery_data"], recovery_data)
            self.assertEqual(result["business_loss_data"], business_loss_data)

            self.assertTrue(os.path.exists(output_path))

            with open(output_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data["incident_id"], incident_id)
            self.assertEqual(loaded_data["sla_data"], sla_data)
            self.assertEqual(loaded_data["recovery_data"], recovery_data)
            self.assertEqual(loaded_data["business_loss_data"], business_loss_data)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            dir_name = os.path.dirname(output_path)
            if dir_name and os.path.exists(dir_name) and not os.listdir(dir_name):
                os.rmdir(dir_name)