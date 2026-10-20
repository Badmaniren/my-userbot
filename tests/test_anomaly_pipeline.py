import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError


class TestAnomalyPipelineInquisition(unittest.TestCase):
    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 4)

    def test_init_robustness_and_fallbacks(self):
        # Fallback branch 1: AnomalyFilter accepts repo_path, AnomalyDetector accepts repo_path, threshold
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d:
            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            mock_f.assert_called_with(repo_path=self.rand_repo)
            mock_d.assert_called_with(repo_path=self.rand_repo, threshold=self.rand_threshold)
            self.assertEqual(pipeline.repo_path, self.rand_repo)
            self.assertEqual(pipeline.threshold, self.rand_threshold)

        # Fallback branch 2: AnomalyFilter raises TypeError on repo_path, succeeds on no args
        with patch("skills.anomaly_pipeline.AnomalyFilter", side_effect=[TypeError("no repo_path"), MagicMock()]) as mock_f, \
             patch("skills.anomaly_pipeline.AnomalyDetector", side_effect=[TypeError("no repo"), MagicMock()]) as mock_d:
            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            self.assertIsNotNone(pipeline.filter_module)
            self.assertIsNotNone(pipeline.detector_module)

    def test_run_success(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_d_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = mock_d_inst

            metric_name = f"metric_{uuid.uuid4().hex}"
            metric_val = round(random.uniform(10.0, 500.0), 3)
            expected_flag = random.choice([True, False])
            raw_input = {f"raw_{uuid.uuid4().hex}": uuid.uuid4().hex}

            mock_f_inst.filter.return_value = {metric_name: metric_val}
            mock_d_inst.detect_anomaly.return_value = expected_flag

            pipeline = AnomalyPipeline(repo_path=self.rand_repo, threshold=self.rand_threshold)
            result = pipeline.run(raw_input)

            mock_f_inst.filter.assert_called_once_with(raw_input)
            mock_d_inst.detect_anomaly.assert_called_once_with(metric_name, metric_val)
            self.assertEqual(result, {
                "is_anomaly": expected_flag,
                "metric_name": metric_name,
                "target_value": metric_val
            })

    def test_run_empty_or_non_dict_filtered(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = MagicMock()

            pipeline = AnomalyPipeline()

            mock_f_inst.filter.return_value = {}
            res_empty = pipeline.run({"dummy": uuid.uuid4().hex})
            self.assertEqual(res_empty, {"is_anomaly": False})

            mock_f_inst.filter.return_value = [uuid.uuid4().hex]
            res_non_dict = pipeline.run({"dummy": uuid.uuid4().hex})
            self.assertEqual(res_non_dict, {"is_anomaly": False})

    def test_run_exceptions_raise_pipeline_error(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_d_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = mock_d_inst

            err_msg_filter = f"filter_failure_{uuid.uuid4().hex}"
            mock_f_inst.filter.side_effect = RuntimeError(err_msg_filter)

            pipeline = AnomalyPipeline()
            with self.assertRaises(AnomalyPipelineError) as cm:
                pipeline.run({"data": uuid.uuid4().hex})
            self.assertIn(err_msg_filter, str(cm.exception))

            mock_f_inst.filter.side_effect = None
            mock_f_inst.filter.return_value = {"metric": 42.0}
            err_msg_detector = f"detector_failure_{uuid.uuid4().hex}"
            mock_d_inst.detect_anomaly.side_effect = ValueError(err_msg_detector)

            with self.assertRaises(AnomalyPipelineError) as cm2:
                pipeline.run({"data": uuid.uuid4().hex})
            self.assertIn(err_msg_detector, str(cm2.exception))

    def test_run_batch_success_and_errors(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_d_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = mock_d_inst

            pipeline = AnomalyPipeline()

            m1, v1 = f"m1_{uuid.uuid4().hex}", round(random.uniform(1.0, 50.0), 2)
            m2, v2 = f"m2_{uuid.uuid4().hex}", round(random.uniform(51.0, 100.0), 2)
            b1, b2 = random.choice([True, False]), random.choice([True, False])

            mock_f_inst.filter.return_value = {m1: v1, m2: v2}

            def detect_side_effect(metric, val):
                if metric == m1 and val == v1:
                    return b1
                if metric == m2 and val == v2:
                    return b2
                return False

            mock_d_inst.detect_anomaly.side_effect = detect_side_effect

            batch_data = {uuid.uuid4().hex: uuid.uuid4().hex}
            res = pipeline.run_batch(batch_data)

            self.assertEqual(res, {m1: b1, m2: b2})
            mock_f_inst.filter.assert_called_with(batch_data)

            err_batch = f"detector_err_{uuid.uuid4().hex}"
            mock_d_inst.detect_anomaly.side_effect = RuntimeError(err_batch)
            with self.assertRaises(AnomalyPipelineError) as cm:
                pipeline.run_batch(batch_data)
            self.assertIn(err_batch, str(cm.exception))

    def test_process_pipeline_flow(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_d_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = mock_d_inst

            pipeline = AnomalyPipeline()

            m_scalar = f"scalar_{uuid.uuid4().hex}"
            val_scalar = random.randint(10, 50)
            flag_scalar = random.choice([True, False])

            m_list = f"list_{uuid.uuid4().hex}"
            val_list = [random.randint(1, 5), random.randint(6, 10)]
            flag_list = random.choice([True, False])

            m_bad = f"bad_{uuid.uuid4().hex}"

            mock_f_inst.filter.return_value = {
                m_scalar: val_scalar,
                m_list: val_list,
                m_bad: "not_a_number"
            }

            def detect_side_effect(metric, val):
                if metric == m_scalar and val == float(val_scalar):
                    return flag_scalar
                if metric == m_list:
                    return flag_list
                raise ValueError("Unexpected metric or invalid value")

            mock_d_inst.detect_anomaly.side_effect = detect_side_effect

            raw_input = {"arbitrary": uuid.uuid4().hex}
            result = pipeline.process_pipeline(raw_input)

            self.assertIn("filtered_data", result)
            self.assertIn("detection_result", result)
            self.assertEqual(result["detection_result"][m_scalar], flag_scalar)
            self.assertEqual(result["detection_result"][m_list], flag_list)
            self.assertFalse(result["detection_result"][m_bad])

    def test_process_pipeline_filter_exception_fallback(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter") as mock_f_cls, \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_f_inst = MagicMock()
            mock_d_inst = MagicMock()
            mock_f_cls.return_value = mock_f_inst
            mock_d_cls.return_value = mock_d_inst

            mock_f_inst.filter.side_effect = Exception("Filter went down")

            pipeline = AnomalyPipeline()
            metric = f"metric_{uuid.uuid4().hex}"
            val = round(random.uniform(1.0, 10.0), 2)
            flag = random.choice([True, False])
            mock_d_inst.detect_anomaly.return_value = flag

            raw_data = {metric: val}
            res = pipeline.process_pipeline(raw_data)

            self.assertEqual(res["filtered_data"], raw_data)
            self.assertEqual(res["detection_result"], {metric: flag})

    def test_run_end_to_end(self):
        with patch("skills.anomaly_pipeline.AnomalyFilter"), \
             patch("skills.anomaly_pipeline.AnomalyDetector") as mock_d_cls:
            mock_d_inst = MagicMock()
            mock_d_cls.return_value = mock_d_inst

            pipeline = AnomalyPipeline()

            m_valid = f"metric_{uuid.uuid4().hex}"
            v_valid = round(random.uniform(5.0, 95.0), 3)
            expected_decision = random.choice([True, False])

            m_invalid = f"invalid_{uuid.uuid4().hex}"

            def detect_side(m, v):
                if m == m_valid and v == float(v_valid):
                    return expected_decision
                raise ValueError("Invalid metric parse")

            mock_d_inst.detect_anomaly.side_effect = detect_side

            execution_id = f"exec_{uuid.uuid4().hex}"
            payload = {
                m_valid: v_valid,
                m_invalid: "invalid_float_literal"
            }

            res = pipeline.run_end_to_end(execution_id, payload)
            self.assertEqual(res[m_valid], expected_decision)
            self.assertFalse(res[m_invalid])


if __name__ == "__main__":
    unittest.main()