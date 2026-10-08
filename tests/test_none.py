import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

# Создаем фальшивые модули в sys.modules до импорта тестируемого модуля,
# чтобы предотвратить ModuleNotFoundError в окружении без установленных сторонних зависимостей.
for mod_name in [
    "db_storage",
    "market_anomaly_detector",
    "market_parser",
    "market_insider_activity_tracker",
    "market_insider_alert_pipeline"
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from skills.none import start_new, create_new_market_anomaly_epic


class TestNoneSkill(unittest.TestCase):

    def setUp(self):
        self.epic_name = f"epic_{uuid.uuid4().hex[:8]}"
        self.target_metric = f"metric_{uuid.uuid4().hex[:8]}"
        self.stream_source = io.BytesIO(uuid.uuid4().bytes)
        self.title = f"title_{uuid.uuid4().hex[:8]}"
        self.report_ref = f"report_{uuid.uuid4().hex[:8]}"

    def test_start_new_success_with_stream(self):
        with patch("db_storage.save_epic") as mock_save_epic, \
             patch("market_anomaly_detector.initialize_system") as mock_init_system, \
             patch("market_parser.parse_stream") as mock_parse_stream, \
             patch("market_insider_alert_pipeline.execute_pipeline", create=True) as mock_execute_pipeline:

            detector_response = f"detector_res_{uuid.uuid4().hex[:6]}"
            pipeline_response = f"pipeline_res_{uuid.uuid4().hex[:6]}"

            mock_init_system.return_value = detector_response
            mock_execute_pipeline.return_value = pipeline_response

            result = start_new(
                epic_name=self.epic_name,
                target_metric=self.target_metric,
                stream_source=self.stream_source
            )

            mock_save_epic.assert_called_once_with(epic_name=self.epic_name, target=self.target_metric)
            mock_init_system.assert_called_once_with(target=self.target_metric)
            mock_parse_stream.assert_called_once_with(self.stream_source)
            mock_execute_pipeline.assert_called_once()

            self.assertEqual(result.get("epic"), self.epic_name)
            self.assertEqual(result.get("target"), self.target_metric)
            self.assertEqual(result.get("detector"), detector_response)
            self.assertEqual(result.get("pipeline_result"), pipeline_response)

    def test_start_new_without_stream_source(self):
        with patch("db_storage.save_epic") as mock_save_epic, \
             patch("market_anomaly_detector.initialize_system") as mock_init_system, \
             patch("market_parser.parse_stream") as mock_parse_stream, \
             patch("market_insider_alert_pipeline.execute_pipeline", create=True) as mock_execute_pipeline:

            detector_response = f"det_{uuid.uuid4().hex[:6]}"
            mock_init_system.return_value = detector_response

            result = start_new(
                epic_name=self.epic_name,
                target_metric=self.target_metric,
                stream_source=None
            )

            mock_save_epic.assert_called_once_with(epic_name=self.epic_name, target=self.target_metric)
            mock_init_system.assert_called_once_with(target=self.target_metric)
            mock_parse_stream.assert_called_once_with()
            self.assertEqual(result.get("epic"), self.epic_name)
            self.assertEqual(result.get("detector"), detector_response)

    def test_start_new_db_storage_raises_runtime_error(self):
        with patch("db_storage.save_epic") as mock_save_epic, \
             patch("market_anomaly_detector.initialize_system") as mock_init_system, \
             patch("market_parser.parse_stream") as mock_parse_stream:

            error_message = f"db_error_{uuid.uuid4().hex[:6]}"
            mock_save_epic.side_effect = RuntimeError(error_message)

            with self.assertRaises(RuntimeError) as context:
                start_new(epic_name=self.epic_name, target_metric=self.target_metric)

            self.assertIn(error_message, str(context.exception))
            mock_init_system.assert_not_called()
            mock_parse_stream.assert_not_called()

    def test_create_new_market_anomaly_epic(self):
        mock_db_instance = MagicMock()
        expected_epic_id = random.randint(1000, 999999)
        mock_db_instance.create_epic_record.return_value = expected_epic_id

        result_id = create_new_market_anomaly_epic(
            title=self.title,
            report_reference=self.report_ref,
            db_instance=mock_db_instance
        )

        mock_db_instance.create_epic_record.assert_called_once_with({
            "title": self.title,
            "report": self.report_ref
        })
        self.assertEqual(result_id, expected_epic_id)


if __name__ == "__main__":
    unittest.main()