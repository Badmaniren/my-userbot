import unittest
from unittest.mock import MagicMock
import uuid
import random

from skills.market_insider_investigation_dossier_builder import start_new


class TestMarketInsiderInvestigationDossierBuilderStartNew(unittest.TestCase):

    def test_start_new_success_all_deps(self):
        target_id = uuid.uuid4().hex

        mock_db = MagicMock()
        mock_db.fetch_investigation_data.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_extractor = MagicMock()
        mock_detector = MagicMock()
        mock_pipeline = MagicMock()
        mock_bridge = MagicMock()

        result = start_new(
            target_id,
            db_storage=mock_db,
            extractor_tool_1790087207=mock_extractor,
            market_anomaly_detector=mock_detector,
            market_insider_alert_pipeline=mock_pipeline,
            market_insider_anomaly_report_bridge=mock_bridge
        )

        mock_db.fetch_investigation_data.assert_called_once_with(target_id)
        mock_extractor.extract.assert_called_once_with(target_id)
        mock_detector.analyze.assert_called_once_with(target_id)
        mock_pipeline.run.assert_called_once_with(target_id)
        mock_bridge.build_report.assert_called_once_with(target_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_id"), target_id)
        self.assertEqual(result.get("status"), "success")

    def test_start_new_db_returns_none(self):
        target_id = uuid.uuid4().hex

        mock_db = MagicMock()
        mock_db.fetch_investigation_data.return_value = None

        mock_extractor = MagicMock()

        result = start_new(
            target_id,
            db_storage=mock_db,
            extractor_tool_1790087207=mock_extractor
        )

        mock_db.fetch_investigation_data.assert_called_once_with(target_id)
        mock_extractor.extract.assert_not_called()
        self.assertIsNone(result)

    def test_start_new_no_dependencies(self):
        target_id = uuid.uuid4().hex

        result = start_new(target_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_id"), target_id)
        self.assertEqual(result.get("status"), "success")


if __name__ == "__main__":
    unittest.main()