import unittest
import uuid
import random
import io
from typing import Any

import skills.none as target_module

try:
    import db_storage
except ImportError:
    from skills import db_storage

try:
    import market_anomaly_detector
except ImportError:
    from skills import market_anomaly_detector

try:
    import market_parser
except ImportError:
    from skills import market_parser

try:
    import market_insider_alert_pipeline
except ImportError:
    from skills import market_insider_alert_pipeline


class MockDBInstance:
    def __init__(self, record_id: str):
        self.record_id = record_id
        self.created_data = None

    def create_epic_record(self, data: dict) -> str:
        self.created_data = data
        return self.record_id


class IntegrationMarketAnomalyEpicTest(unittest.TestCase):

    def test_start_new_and_create_epic_integration(self):
        epic_name = f"epic_test_{uuid.uuid4()}"
        target_metric = f"metric_{random.randint(1000, 9999)}"
        stream_source = io.BytesIO(f"market_data_stream_{uuid.uuid4()}".encode("utf-8"))

        result = target_module.start_new(
            epic_name=epic_name,
            target_metric=target_metric,
            stream_source=stream_source
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("epic"), epic_name)
        self.assertEqual(result.get("target"), target_metric)
        self.assertIn("detector", result)
        self.assertIn("pipeline_result", result)

        expected_record_id = str(uuid.uuid4())
        title = f"Title_{uuid.uuid4()}"
        report_reference = f"report_ref_{uuid.uuid4()}"
        mock_db = MockDBInstance(expected_record_id)

        returned_id = target_module.create_new_market_anomaly_epic(
            title=title,
            report_reference=report_reference,
            db_instance=mock_db
        )

        self.assertEqual(returned_id, expected_record_id)
        self.assertIsNotNone(mock_db.created_data)
        self.assertEqual(mock_db.created_data.get("title"), title)
        self.assertEqual(mock_db.created_data.get("report"), report_reference)


if __name__ == "__main__":
    unittest.main()
