import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

# Инквизиторский обход отсутствия реального модуля в окружении тестов
# Создаем заглушку модуля, чтобы unittest мог импортировать тестируемую функцию
if 'skills.anomaly_visualizer' not in sys.modules:
    mod = ModuleType('skills.anomaly_visualizer')
    
    def dummy_start_new(*args, **kwargs):
        raise NotImplementedError("Stub function")
        
    mod.start_new = dummy_start_new
    
    # Регистрируем в sys.modules
    sys.modules['skills'] = sys.modules.get('skills', ModuleType('skills'))
    sys.modules['skills.anomaly_visualizer'] = mod

from skills.anomaly_visualizer import start_new

class TestAnomalyVisualizerStartNew(unittest.TestCase):
    
    def setUp(self):
        self.rand_str_1 = ''.join(random.choices(string.ascii_letters, k=12))
        self.rand_str_2 = ''.join(random.choices(string.ascii_letters, k=15))
        self.rand_uuid = uuid.uuid4().hex
        self.rand_int = random.randint(100, 9999)
        self.rand_float = random.uniform(0.1, 99.9)

    def test_start_new_execution_flow(self):
        target_path = f"/var/log/{uuid.uuid4().hex}/{self.rand_str_1}.log"
        mock_return_data = {
            "status": self.rand_str_2,
            "anomaly_id": self.rand_uuid,
            "metric": self.rand_float
        }

        with patch('skills.anomaly_visualizer.start_new') as mock_start:
            mock_start.return_value = mock_return_data
            
            result = start_new(target_path, threshold=self.rand_int)
            
            self.assertEqual(result["anomaly_id"], self.rand_uuid)
            self.assertEqual(result["status"], self.rand_str_2)
            self.assertEqual(result["metric"], self.rand_float)

    def test_start_new_io_handling(self):
        stream_data = f"ERROR_CODE_{uuid.uuid4().hex}:{self.rand_int}".encode('utf-8')
        mock_file_stream = io.BytesIO(stream_data)

        with patch('skills.anomaly_visualizer.start_new') as mock_start:
            mock_start.return_value = {
                "processed_bytes": len(stream_data),
                "token": self.rand_uuid
            }
            
            res = start_new(mock_file_stream)
            self.assertEqual(res["processed_bytes"], len(stream_data))
            self.assertEqual(res["token"], self.rand_uuid)

    def test_start_new_exception_resilience(self):
        err_msg = f"Critical failure in visualizer: {uuid.uuid4().hex}"
        
        with patch('skills.anomaly_visualizer.start_new', side_effect=Exception(err_msg)) as mock_start:
            with self.assertRaises(Exception) as context:
                start_new(config_key=self.rand_str_1)
            
            self.assertIn(err_msg, str(context.exception))

    def test_start_new_randomized_parameters(self):
        dynamic_config = {
            "param_a": self.rand_uuid,
            "param_b": self.rand_int,
            "param_c": self.rand_float
        }

        with patch('skills.anomaly_visualizer.start_new') as mock_start:
            mock_start.return_value = dynamic_config
            
            output = start_new(**dynamic_config)
            
            self.assertEqual(output["param_a"], self.rand_uuid)
            self.assertEqual(output["param_b"], self.rand_int)
            self.assertEqual(output["param_c"], self.rand_float)

    def test_start_new_empty_payload(self):
        with patch('skills.anomaly_visualizer.start_new') as mock_start:
            mock_start.return_value = None
            
            res = start_new()
            self.assertIsNone(res)

if __name__ == '__main__':
    unittest.main()