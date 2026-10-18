import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = uuid.uuid4().hex
        self.threshold = random.uniform(0.1, 0.9)

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_init_success(self, mock_filter_cls, mock_detector_cls):
        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        self.assertEqual(pipeline.repo_path, self.repo_path)
        self.assertEqual(pipeline.threshold, self.threshold)
        mock_filter_cls.assert_called_once()
        mock_detector_cls.assert_called_once()

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_normal_anomaly(self, mock_filter_cls, mock_detector_cls):
        metric_name = uuid.uuid4().hex
        target_val = random.uniform(1.0, 100.0)
        is_anomaly_expected = random.choice([True, False])

        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.return_value = {metric_name: target_val}

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.return_value = is_anomaly_expected

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        raw_input = {uuid.uuid4().hex: random.randint(1, 500)}
        result = pipeline.run(raw_input)

        expected_result = {
            "is_anomaly": is_anomaly_expected,
            "metric_name": metric_name,
            "target_value": target_val
        }
        self.assertEqual(result, expected_result)
        mock_filter_instance.filter.assert_called_once_with(raw_input)
        mock_detector_instance.detect_anomaly.assert_called_once_with(metric_name, target_val)

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_empty_filtered(self, mock_filter_cls, mock_detector_cls):
        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.return_value = {}

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        raw_input = uuid.uuid4().hex
        result = pipeline.run(raw_input)

        self.assertEqual(result, {"is_anomaly": False})

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_filter_exception(self, mock_filter_cls, mock_detector_cls):
        err_msg = uuid.uuid4().hex
        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.side_effect = Exception(err_msg)

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        with self.assertRaises(AnomalyPipelineError) as ctx:
            pipeline.run(uuid.uuid4().hex)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_detector_exception(self, mock_filter_cls, mock_detector_cls):
        metric_name = uuid.uuid4().hex
        target_val = random.uniform(10.0, 50.0)
        err_msg = uuid.uuid4().hex

        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.return_value = {metric_name: target_val}

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.side_effect = Exception(err_msg)

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        with self.assertRaises(AnomalyPipelineError) as ctx:
            pipeline.run(uuid.uuid4().hex)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_batch_success(self, mock_filter_cls, mock_detector_cls):
        k1, k2 = uuid.uuid4().hex, uuid.uuid4().hex
        v1, v2 = random.random(), random.random()
        anom1, anom2 = random.choice([True, False]), random.choice([True, False])

        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.return_value = {k1: v1, k2: v2}

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.side_effect = [anom1, anom2]

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        result = pipeline.run_batch(uuid.uuid4().hex)

        self.assertEqual(result, {k1: anom1, k2: anom2})

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_batch_filter_exception(self, mock_filter_cls, mock_detector_cls):
        err_msg = uuid.uuid4().hex
        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.side_effect = Exception(err_msg)

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        with self.assertRaises(AnomalyPipelineError) as ctx:
            pipeline.run_batch(uuid.uuid4().hex)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_process_pipeline_success(self, mock_filter_cls, mock_detector_cls):
        k1 = uuid.uuid4().hex
        v_list = [random.randint(1, 10), random.randint(11, 20)]
        is_anom = random.choice([True, False])

        mock_filter_instance = mock_filter_cls.return_value
        filtered_data = {k1: v_list}
        mock_filter_instance.filter.return_value = filtered_data

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.return_value = is_anom

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        result = pipeline.process_pipeline(uuid.uuid4().hex)

        expected_output = {
            "filtered_data": filtered_data,
            "detection_result": {k1: is_anom}
        }
        self.assertEqual(result, expected_output)
        mock_detector_instance.detect_anomaly.assert_called_with(k1, float(v_list[-1]))

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_process_pipeline_filter_fails_falls_back(self, mock_filter_cls, mock_detector_cls):
        k1 = uuid.uuid4().hex
        v_scalar = random.randint(100, 200)
        fallback_data = {k1: v_scalar}
        is_anom = random.choice([True, False])

        mock_filter_instance = mock_filter_cls.return_value
        mock_filter_instance.filter.side_effect = Exception(uuid.uuid4().hex)

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.return_value = is_anom

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        result = pipeline.process_pipeline(fallback_data)

        expected_output = {
            "filtered_data": fallback_data,
            "detection_result": {k1: is_anom}
        }
        self.assertEqual(result, expected_output)

    @patch('skills.anomaly_pipeline.AnomalyDetector')
    @patch('skills.anomaly_pipeline.AnomalyFilter')
    def test_run_end_to_end_success(self, mock_filter_cls, mock_detector_cls):
        exec_id = uuid.uuid4().hex
        k1, k2 = uuid.uuid4().hex, uuid.uuid4().hex
        v1, v2 = random.random(), random.random()
        anom1, anom2 = random.choice([True, False]), random.choice([True, False])

        mock_detector_instance = mock_detector_cls.return_value
        mock_detector_instance.detect_anomaly.side_effect = [anom1, anom2]

        pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)
        payload = {k1: v1, k2: v2}
        result = pipeline.run_end_to_end(exec_id, payload)

        self.assertEqual(result, {k1: anom1, k2: anom2})
        mock_detector_instance.detect_anomaly.assert_any_call(k1, float(v1))
        mock_detector_instance.detect_anomaly.assert_any_call(k2, float(v2))


if __name__ == '__main__':
    unittest.main()