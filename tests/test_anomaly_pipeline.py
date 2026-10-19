import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


def _rand_str(length=8):
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def _rand_float(min_val=0.1, max_val=100.0):
    return round(random.uniform(min_val, max_val), 4)


class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_threshold = _rand_float(1.0, 50.0)

    def test_init_fallback_filter_and_detector(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_cls.side_effect = [TypeError("No zero-args"), MagicMock()]
            mock_detector_cls.side_effect = [TypeError("No both"), TypeError("No thresh"), MagicMock()]

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)

            self.assertEqual(pipeline.repo_path, self.rand_repo)
            self.assertEqual(pipeline.threshold, self.rand_threshold)
            mock_filter_cls.assert_any_call(repo_path=self.rand_repo)
            mock_detector_cls.assert_called_with()

    def test_init_detector_with_threshold_fallback(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_detector_cls.side_effect = [TypeError("Repo not accepted"), MagicMock()]

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)

            self.assertEqual(pipeline.repo_path, self.rand_repo)
            self.assertEqual(pipeline.threshold, self.rand_threshold)
            mock_detector_cls.assert_called_with(threshold=self.rand_threshold)

    def test_run_success(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            metric_name = f"metric_{uuid.uuid4().hex[:6]}"
            target_value = _rand_float()
            is_anomaly_expected = random.choice([True, False])
            raw_input_data = {f"raw_{uuid.uuid4().hex[:4]}": _rand_str()}

            mock_filter_inst.filter.return_value = {metric_name: target_value}
            mock_detector_inst.detect_anomaly.return_value = is_anomaly_expected

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            result = pipeline.run(raw_input_data)

            mock_filter_inst.filter.assert_called_once_with(raw_input_data)
            mock_detector_inst.detect_anomaly.assert_called_once_with(metric_name, target_value)

            self.assertEqual(result["is_anomaly"], is_anomaly_expected)
            self.assertEqual(result["metric_name"], metric_name)
            self.assertEqual(result["target_value"], target_value)

    def test_run_empty_filtered(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            mock_filter_inst.filter.return_value = random.choice([{}, None, []])

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            result = pipeline.run({uuid.uuid4().hex: uuid.uuid4().hex})

            self.assertEqual(result, {"is_anomaly": False})
            mock_detector_inst.detect_anomaly.assert_not_called()

    def test_run_filter_exception_raises_pipeline_error(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector"):

            mock_filter_inst = MagicMock()
            err_msg = f"Filter crash {uuid.uuid4().hex}"
            mock_filter_inst.filter.side_effect = RuntimeError(err_msg)
            mock_filter_cls.return_value = mock_filter_inst

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)

            with self.assertRaises(AnomalyPipelineError) as ctx:
                pipeline.run({"dummy": uuid.uuid4().hex})

            self.assertIn(err_msg, str(ctx.exception))

    def test_run_detector_exception_raises_pipeline_error(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            metric_name = f"metric_{uuid.uuid4().hex[:6]}"
            target_value = _rand_float()
            mock_filter_inst.filter.return_value = {metric_name: target_value}

            err_msg = f"Detector explosion {uuid.uuid4().hex}"
            mock_detector_inst.detect_anomaly.side_effect = ValueError(err_msg)

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)

            with self.assertRaises(AnomalyPipelineError) as ctx:
                pipeline.run({metric_name: target_value})

            self.assertIn(err_msg, str(ctx.exception))

    def test_run_batch_success(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            num_metrics = random.randint(2, 5)
            filtered_data = {
                f"metric_{uuid.uuid4().hex[:6]}": _rand_float()
                for _ in range(num_metrics)
            }
            expected_results = {}
            for k in filtered_data:
                decision = random.choice([True, False])
                expected_results[k] = decision

            def detect_side_effect(metric, val):
                return expected_results[metric]

            mock_filter_inst.filter.return_value = filtered_data
            mock_detector_inst.detect_anomaly.side_effect = detect_side_effect

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            batch_input = {f"in_{uuid.uuid4().hex[:4]}": _rand_str()}
            batch_result = pipeline.run_batch(batch_input)

            mock_filter_inst.filter.assert_called_once_with(batch_input)
            self.assertEqual(batch_result, expected_results)

    def test_run_batch_filter_error(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector"):

            mock_filter_inst = MagicMock()
            err_text = f"Batch filter error {uuid.uuid4().hex}"
            mock_filter_inst.filter.side_effect = Exception(err_text)
            mock_filter_cls.return_value = mock_filter_inst

            pipeline = AnomalyPipeline()
            with self.assertRaises(AnomalyPipelineError) as ctx:
                pipeline.run_batch({"item": 123})

            self.assertIn(err_text, str(ctx.exception))

    def test_run_batch_detector_error(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            m_name = f"m_{uuid.uuid4().hex[:4]}"
            mock_filter_inst.filter.return_value = {m_name: 12.3}
            err_msg = f"Detector failure {uuid.uuid4().hex}"
            mock_detector_inst.detect_anomaly.side_effect = RuntimeError(err_msg)

            pipeline = AnomalyPipeline()
            with self.assertRaises(AnomalyPipelineError) as ctx:
                pipeline.run_batch({m_name: 12.3})

            self.assertIn(err_msg, str(ctx.exception))

    def test_process_pipeline_handles_filter_exception_and_lists(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            mock_filter_inst.filter.side_effect = RuntimeError("Filtering not available")

            metric_single = f"single_{uuid.uuid4().hex[:4]}"
            metric_list = f"list_{uuid.uuid4().hex[:4]}"
            metric_invalid = f"invalid_{uuid.uuid4().hex[:4]}"

            val_single = _rand_float()
            val_list_items = [_rand_float(), _rand_float()]

            raw_data = {
                metric_single: val_single,
                metric_list: val_list_items,
                metric_invalid: f"not_a_number_{uuid.uuid4().hex[:4]}"
            }

            def detect_side_effect(metric, val):
                if metric == metric_single:
                    return True
                if metric == metric_list:
                    return val == float(val_list_items[-1])
                return False

            mock_detector_inst.detect_anomaly.side_effect = detect_side_effect

            pipeline = AnomalyPipeline()
            res = pipeline.process_pipeline(raw_data)

            self.assertEqual(res["filtered_data"], raw_data)
            self.assertTrue(res["detection_result"][metric_single])
            self.assertTrue(res["detection_result"][metric_list])
            self.assertFalse(res["detection_result"][metric_invalid])

    def test_process_pipeline_detector_exception_fallback(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_filter_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_filter_inst = MagicMock()
            mock_detector_inst = MagicMock()
            mock_filter_cls.return_value = mock_filter_inst
            mock_detector_cls.return_value = mock_detector_inst

            metric_name = f"faulty_{uuid.uuid4().hex[:4]}"
            mock_filter_inst.filter.return_value = {metric_name: _rand_float()}
            mock_detector_inst.detect_anomaly.side_effect = Exception("Detector exploded")

            pipeline = AnomalyPipeline()
            res = pipeline.process_pipeline({"any": "thing"})

            self.assertIn(metric_name, res["detection_result"])
            self.assertFalse(res["detection_result"][metric_name])

    def test_run_end_to_end(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter"), \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_detector_inst = MagicMock()
            mock_detector_cls.return_value = mock_detector_inst

            metric_ok = f"ok_{uuid.uuid4().hex[:4]}"
            metric_bad = f"bad_{uuid.uuid4().hex[:4]}"
            exec_id = f"exec_{uuid.uuid4().hex}"

            payload = {
                metric_ok: _rand_float(),
                metric_bad: f"corrupt_{uuid.uuid4().hex}"
            }

            expected_decision = random.choice([True, False])

            def detect_logic(name, val):
                if name == metric_ok:
                    return expected_decision
                raise ValueError("Bad metric")

            mock_detector_inst.detect_anomaly.side_effect = detect_logic

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            results = pipeline.run_end_to_end(exec_id, payload)

            self.assertIn(metric_ok, results)
            self.assertEqual(results[metric_ok], expected_decision)
            self.assertIn(metric_bad, results)
            self.assertFalse(results[metric_bad])

    def test_run_end_to_end_non_dict_payload(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter"), \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_detector_cls:

            mock_detector_inst = MagicMock()
            mock_detector_cls.return_value = mock_detector_inst

            pipeline = AnomalyPipeline()
            res = pipeline.run_end_to_end(uuid.uuid4().hex, None)

            self.assertEqual(res, {})
            mock_detector_inst.detect_anomaly.assert_not_called()


if __name__ == "__main__":
    unittest.main()