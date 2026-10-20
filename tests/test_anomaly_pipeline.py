import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/{uuid.uuid4().hex}"
        self.random_threshold = random.uniform(0.1, 0.9)
        self.metric_key = uuid.uuid4().hex
        self.metric_value = random.randint(10, 100)

    def test_pipeline_initialization_variants(self):
        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector:

            pipeline = AnomalyPipeline(repo_path=self.random_repo, threshold=self.random_threshold)
            self.assertIsInstance(pipeline, AnomalyPipeline)

            pipeline_no_args = AnomalyPipeline()
            self.assertIsInstance(pipeline_no_args, AnomalyPipeline)

    def test_run_success(self):
        raw_input = {self.metric_key: self.metric_value}

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = raw_input

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.return_value = True

            pipeline = AnomalyPipeline(repo_path=self.random_repo, threshold=self.random_threshold)
            result = pipeline.run(raw_input)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["metric_name"], self.metric_key)
            self.assertEqual(result["target_value"], self.metric_value)

    def test_run_empty_filtered(self):
        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = {}

            pipeline = AnomalyPipeline()
            result = pipeline.run(uuid.uuid4().hex)

            self.assertFalse(result["is_anomaly"])

    def test_run_pipeline_error(self):
        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.side_effect = Exception(uuid.uuid4().hex)

            pipeline = AnomalyPipeline()
            with self.assertRaises(AnomalyPipelineError):
                pipeline.run(uuid.uuid4().hex)

    def test_run_batch(self):
        raw_batch = {uuid.uuid4().hex: random.randint(1, 50), uuid.uuid4().hex: random.randint(51, 100)}

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = raw_batch

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.side_effect = [True, False]

            pipeline = AnomalyPipeline(threshold=self.random_threshold)
            results = pipeline.run_batch(raw_batch)

            self.assertIn(list(raw_batch.keys())[0], results)
            self.assertTrue(results[list(raw_batch.keys())[0]])

    def test_process_pipeline(self):
        k1 = uuid.uuid4().hex
        v1 = random.randint(1, 100)
        raw_data = {k1: v1}

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_filter_instance = mock_filter_cls.return_value
            mock_filter_instance.filter.return_value = raw_data

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.return_value = True

            pipeline = AnomalyPipeline()
            output = pipeline.process_pipeline(raw_data)

            self.assertEqual(output["filtered_data"], raw_data)
            self.assertTrue(output["detection_result"][k1])

    def test_run_end_to_end(self):
        payload = {uuid.uuid4().hex: random.uniform(1.0, 10.0)}

        with patch('skills.anomaly_pipeline.AnomalyFilter') as mock_filter_cls, \
             patch('skills.anomaly_pipeline.AnomalyDetector') as mock_detector_cls:

            mock_detector_instance = mock_detector_cls.return_value
            mock_detector_instance.detect_anomaly.return_value = False

            pipeline = AnomalyPipeline(repo_path=self.random_repo)
            res = pipeline.run_end_to_end(uuid.uuid4().hex, payload)

            self.assertFalse(res[list(payload.keys())[0]])


if __name__ == '__main__':
    unittest.main()