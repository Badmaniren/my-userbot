import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)

        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector:
            
            self.pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            self.mock_filter_instance = mock_filter.return_value
            self.mock_detector_instance = mock_detector.return_value

    def test_run_success(self):
        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_val = random.randint(10, 100)
        rand_is_anom = random.choice([True, False])

        self.mock_filter_instance.filter.return_value = {rand_metric: rand_val}
        self.mock_detector_instance.detect_anomaly.return_value = rand_is_anom

        raw_in = {uuid.uuid4().hex: random.randint(1, 5)}
        res = self.pipeline.run(raw_in)

        self.assertEqual(res["is_anomaly"], rand_is_anom)
        self.assertEqual(res["metric_name"], rand_metric)
        self.assertEqual(res["target_value"], rand_val)
        self.mock_filter_instance.filter.assert_called_once_with(raw_in)
        self.mock_detector_instance.detect_anomaly.assert_called_once_with(rand_metric, rand_val)

    def test_run_filter_empty(self):
        self.mock_filter_instance.filter.return_value = {}
        raw_in = uuid.uuid4().hex
        res = self.pipeline.run(raw_in)
        self.assertEqual(res, {"is_anomaly": False})

    def test_run_filter_exception(self):
        rand_err_msg = uuid.uuid4().hex
        self.mock_filter_instance.filter.side_effect = Exception(rand_err_msg)

        with self.assertRaises(AnomalyPipelineError) as ctx:
            self.pipeline.run(uuid.uuid4().hex)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_run_detector_exception(self):
        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_val = random.randint(10, 100)
        rand_err_msg = uuid.uuid4().hex

        self.mock_filter_instance.filter.return_value = {rand_metric: rand_val}
        self.mock_detector_instance.detect_anomaly.side_effect = Exception(rand_err_msg)

        with self.assertRaises(AnomalyPipelineError) as ctx:
            self.pipeline.run(uuid.uuid4().hex)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_run_batch_success(self):
        m1 = f"m_{uuid.uuid4().hex[:4]}"
        m2 = f"m_{uuid.uuid4().hex[:4]}"
        v1 = random.randint(1, 50)
        v2 = random.randint(51, 100)
        res1 = random.choice([True, False])
        res2 = random.choice([True, False])

        self.mock_filter_instance.filter.return_value = {m1: v1, m2: v2}

        def side_effect_detect(metric, val):
            if metric == m1:
                return res1
            return res2

        self.mock_detector_instance.detect_anomaly.side_effect = side_effect_detect

        batch_data = [uuid.uuid4().hex, uuid.uuid4().hex]
        output = self.pipeline.run_batch(batch_data)

        self.assertEqual(output, {m1: res1, m2: res2})
        self.mock_filter_instance.filter.assert_called_once_with(batch_data)

    def test_run_batch_detector_exception(self):
        m1 = f"m_{uuid.uuid4().hex[:4]}"
        v1 = random.randint(1, 50)
        rand_err_msg = uuid.uuid4().hex

        self.mock_filter_instance.filter.return_value = {m1: v1}
        self.mock_detector_instance.detect_anomaly.side_effect = Exception(rand_err_msg)

        with self.assertRaises(AnomalyPipelineError):
            self.pipeline.run_batch(uuid.uuid4().hex)

    def test_process_pipeline_with_lists(self):
        m1 = f"m_{uuid.uuid4().hex[:4]}"
        val1 = random.randint(10, 50)
        val2 = random.randint(51, 100)
        expected_flag = random.choice([True, False])

        filtered_mock = {m1: [val1, val2]}
        self.mock_filter_instance.filter.return_value = filtered_mock
        self.mock_detector_instance.detect_anomaly.return_value = expected_flag

        raw_data = uuid.uuid4().hex
        output = self.pipeline.process_pipeline(raw_data)

        self.assertEqual(output["filtered_data"], filtered_mock)
        self.assertIn(m1, output["detection_result"])
        self.mock_detector_instance.detect_anomaly.assert_called_with(m1, float(val2))

    def test_process_pipeline_filter_exception_fallback(self):
        self.mock_filter_instance.filter.side_effect = Exception(uuid.uuid4().hex)

        m_name = f"metric_{uuid.uuid4().hex[:4]}"
        m_val = random.randint(100, 500)
        raw_data = {m_name: m_val}

        expected_flag = random.choice([True, False])
        self.mock_detector_instance.detect_anomaly.return_value = expected_flag

        output = self.pipeline.process_pipeline(raw_data)

        self.assertEqual(output["filtered_data"], raw_data)
        self.assertEqual(output["detection_result"][m_name], expected_flag)

    def test_run_end_to_end(self):
        m1 = f"m_{uuid.uuid4().hex[:4]}"
        v1 = random.randint(1, 100)
        exec_id = uuid.uuid4().hex
        is_anom = random.choice([True, False])

        self.mock_detector_instance.detect_anomaly.return_value = is_anom

        payload = {m1: v1}
        results = self.pipeline.run_end_to_end(exec_id, payload)

        self.assertEqual(results, {m1: is_anom})
        self.mock_detector_instance.detect_anomaly.assert_called_once_with(m1, float(v1))


if __name__ == "__main__":
    unittest.main()