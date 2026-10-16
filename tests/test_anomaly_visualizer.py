import unittest
from unittest.mock import patch, mock_open
import io
import os
import random
import uuid
from skills.anomaly_visualizer import start_new, AnomalyVisualizer


class TestAnomalyVisualizerStartNew(unittest.TestCase):

    def setUp(self):
        self.rand_str = uuid.uuid4().hex
        self.rand_int = random.randint(100, 999)
        self.token_val = uuid.uuid4().hex

    def test_start_new_io_handling(self):
        payload_bytes = self.rand_str.encode('utf-8')
        mock_file_stream = io.BytesIO(payload_bytes)
        
        res = start_new(mock_file_stream, token=self.token_val)
        
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("processed_bytes"), len(payload_bytes))
        self.assertEqual(res.get("token"), self.token_val)

    def test_start_new_execution_flow(self):
        target_path = f"/var/log/{uuid.uuid4().hex}.log"
        
        result = start_new(target_path, threshold=self.rand_int)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("target_path"), target_path)
        self.assertEqual(result.get("threshold"), self.rand_int)

    def test_start_new_randomized_parameters(self):
        dynamic_config = {
            f"param_{uuid.uuid4().hex[:6]}": random.randint(1, 1000),
            f"key_{uuid.uuid4().hex[:6]}": uuid.uuid4().hex
        }
        
        output = start_new(**dynamic_config)
        
        self.assertEqual(output, dynamic_config)

    def test_start_new_empty_payload(self):
        res = start_new()
        self.assertIsNone(res)


class TestAnomalyVisualizerClass(unittest.TestCase):

    def setUp(self):
        self.output_dir = f"./tmp_{uuid.uuid4().hex[:8]}"
        self.filename = f"report_{uuid.uuid4().hex[:8]}.html"
        self.visualizer = AnomalyVisualizer(output_dir=self.output_dir)

    def tearDown(self):
        report_path = os.path.join(self.output_dir, self.filename)
        if os.path.exists(report_path):
            os.remove(report_path)
        if os.path.exists(self.output_dir):
            os.rmdir(self.output_dir)

    def test_generate_statistical_report(self):
        data_points = [random.random() for _ in range(random.randint(5, 15))]
        run_id_val = uuid.uuid4().hex
        score_val = round(random.uniform(0.1, 99.9), 2)
        
        metadata = {
            "run_id": run_id_val,
            "score": score_val,
            "extra_tag": uuid.uuid4().hex
        }

        report_path = self.visualizer.generate_statistical_report(
            data=data_points,
            filename=self.filename,
            metadata=metadata
        )

        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(f"Data points: {len(data_points)}", content)
        self.assertIn(run_id_val, content)
        self.assertIn(str(score_val), content)
        self.assertIn(metadata["extra_tag"], content)


if __name__ == "__main__":
    unittest.main()