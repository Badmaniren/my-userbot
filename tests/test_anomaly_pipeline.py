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
        self.pipeline_id = uuid.uuid4().hex
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.threshold = round(random.uniform(0.1, 0.9), 2)

    def test_pipeline_initialization_success(self):
        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            mock_detector_instance = mock_detector_cls.return_value

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            
            self.assertIsNotNone(pipeline)
            mock_filter_cls.assert_called_once()
            mock_detector_cls.assert_called_once_with(repo_path=self.repo_path, threshold=self.threshold)

    def test_run_pipeline_end_to_end_anomaly_detected(self):
        raw_data_key = uuid.uuid4().hex
        raw_data_val = random.randint(100, 999)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_val = float(random.randint(1000, 5000))

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            filtered_payload = {metric_name: target_val}
            mock_filter_instance.filter.return_value = filtered_payload

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.return_value = True

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            raw_input = {raw_data_key: raw_data_val}
            
            result = pipeline.run(raw_input)

            mock_filter_instance.filter.assert_called_once_with(raw_input)
            mock_detector_instance.detect_anomaly.assert_called_once_with(metric_name, target_val)
            
            self.assertIn("is_anomaly", result)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["metric_name"], metric_name)
            self.assertEqual(result["target_value"], target_val)

    def test_run_pipeline_end_to_end_no_anomaly(self):
        raw_data_key = uuid.uuid4().hex
        raw_data_val = random.randint(1, 99)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_val = float(random.randint(10, 50))

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            filtered_payload = {metric_name: target_val}
            mock_filter_instance.filter.return_value = filtered_payload

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.return_value = False

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            raw_input = {raw_data_key: raw_data_val}
            
            result = pipeline.run(raw_input)

            mock_filter_instance.filter.assert_called_once_with(raw_input)
            mock_detector_instance.detect_anomaly.assert_called_once_with(metric_name, target_val)
            
            self.assertIn("is_anomaly", result)
            self.assertFalse(result["is_anomaly"])

    def test_pipeline_filter_exception_handling(self):
        invalid_input_key = uuid.uuid4().hex
        invalid_input_val = uuid.uuid4().hex

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.side_effect = ValueError(uuid.uuid4().hex)

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            raw_input = {invalid_input_key: invalid_input_val}

            with self.assertRaises(AnomalyPipelineError):
                pipeline.run(raw_input)

    def test_pipeline_detector_exception_handling(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_val = float(random.randint(100, 500))

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = {metric_name: target_val}

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.side_effect = RuntimeError(uuid.uuid4().hex)

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            raw_input = {uuid.uuid4().hex: uuid.uuid4().hex}

            with self.assertRaises(AnomalyPipelineError):
                pipeline.run(raw_input)

    def test_batch_pipeline_execution(self):
        batch_id = uuid.uuid4().hex
        metric_name_1 = f"metric_{uuid.uuid4().hex[:4]}"
        metric_name_2 = f"metric_{uuid.uuid4().hex[:4]}"
        val_1 = float(random.randint(1, 50))
        val_2 = float(random.randint(51, 100))

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:
            
            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = {
                metric_name_1: val_1,
                metric_name_2: val_2
            }

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.side_effect = [True, False]

            pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
            raw_batch_data = {uuid.uuid4().hex: uuid.uuid4().hex}

            results = pipeline.run_batch(raw_batch_data)

            self.assertEqual(len(results), 2)
            self.assertTrue(results[metric_name_1])
            self.assertFalse(results[metric_name_2])