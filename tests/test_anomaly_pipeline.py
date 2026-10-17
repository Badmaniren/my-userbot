import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError
from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector


class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_threshold = random.uniform(0.1, 99.9)

    @patch('skills.anomaly_pipeline.AnomalyFilter')
    @patch('skills.anomaly_pipeline.AnomalyDetector')
    def test_pipeline_initialization_success(self, mock_detector_cls, mock_filter_cls):
        instance = AnomalyPipeline(repo_path=self.random_repo_path, threshold=self.random_threshold)

        mock_filter_cls.assert_called_once()
        mock_detector_cls.assert_called_once_with(
            repo_path=self.random_repo_path,
            threshold=self.random_threshold,
            git_inspector=None,
            patch_verifier=None
        )
        self.assertIsInstance(instance, AnomalyPipeline)

    @patch('skills.anomaly_pipeline.AnomalyFilter')
    @patch('skills.anomaly_pipeline.AnomalyDetector')
    def test_process_telemetry_filters_and_detects(self, mock_detector_cls, mock_filter_cls):
        mock_filter_instance = mock_filter_cls.return_value
        mock_detector_instance = mock_detector_cls.return_value

        raw_data_id = uuid.uuid4().hex
        filtered_data = {
            "metric": self.random_metric_name,
            "value": random.uniform(1.0, 100.0),
            "id": raw_data_id
        }

        mock_filter_instance.filter.return_value = filtered_data
        mock_detector_instance.detect_anomaly.return_value = True

        pipeline = AnomalyPipeline(repo_path=self.random_repo_path, threshold=self.random_threshold)

        input_payload = {"raw": raw_data_id}
        result = pipeline.process_telemetry(input_payload)

        mock_filter_instance.filter.assert_called_once_with(input_payload)
        mock_detector_instance.record_metric.assert_called_once_with(
            self.random_metric_name, filtered_data["value"]
        )
        mock_detector_instance.detect_anomaly.assert_called_once_with(
            self.random_metric_name, filtered_data["value"]
        )

        self.assertIn("is_anomaly", result)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["metric_name"], self.random_metric_name)
        self.assertEqual(result["target_value"], filtered_data["value"])

    @patch('skills.anomaly_pipeline.AnomalyFilter')
    @patch('skills.anomaly_pipeline.AnomalyDetector')
    def test_process_telemetry_empty_filter_result(self, mock_detector_cls, mock_filter_cls):
        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.return_value = None

        pipeline = AnomalyPipeline(repo_path=self.random_repo_path, threshold=self.random_threshold)

        input_payload = {"ignored": uuid.uuid4().hex}
        result = pipeline.process_telemetry(input_payload)

        mock_filter_instance.filter.assert_called_once_with(input_payload)
        mock_detector_cls.return_value.detect_anomaly.assert_not_called()
        self.assertIsNone(result)

    @patch('skills.anomaly_pipeline.AnomalyFilter')
    @patch('skills.anomaly_pipeline.AnomalyDetector')
    def test_process_telemetry_raises_pipeline_error(self, mock_detector_cls, mock_filter_cls):
        mock_filter_instance = mock_filter_cls.return_value
        random_error_message = f"error_{uuid.uuid4().hex}"
        mock_filter_instance.filter.side_effect = Exception(random_error_message)

        pipeline = AnomalyPipeline(repo_path=self.random_repo_path, threshold=self.random_threshold)

        with self.assertRaises(AnomalyPipelineError) as ctx:
            pipeline.process_telemetry({"data": uuid.uuid4().hex})

        self.assertIn(random_error_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()