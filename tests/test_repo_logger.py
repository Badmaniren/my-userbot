import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import logging
from skills.repo_logger import RepoLogger

class TestRepoLogger(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.logger_instance = RepoLogger(self.repo_path)

    def test_init_sets_repo_path(self):
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        logger = RepoLogger(random_path)
        self.assertEqual(logger.repo_path, random_path)

    def test_log_event_success(self):
        event_name = f"event_{uuid.uuid4().hex[:8]}"
        event_details = f"details_{uuid.uuid4().hex}"
        
        with patch('logging.Logger.info') as mock_info:
            result = self.logger_instance.log_event(event_name, event_details)
            self.assertTrue(result)
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            self.assertIn(event_name, args[0])
            self.assertIn(event_details, args[0])
            self.assertIn(self.repo_path, args[0])

    def test_log_git_operation_propagates_exception_no_silencing(self):
        operation_name = f"git_{uuid.uuid4().hex[:6]}"
        err_message = f"git_error_{uuid.uuid4().hex}"
        
        with patch('logging.Logger.error', side_effect=Exception(err_message)) as mock_error:
            with self.assertRaises(Exception) as ctx:
                self.logger_instance.log_git_operation(operation_name, status="failed")
            self.assertEqual(str(ctx.exception), err_message)
            mock_error.assert_called_once()

    def test_log_error_records_correctly(self):
        error_code = ''.join(random.choices(string.ascii_uppercase, k=5))
        error_msg = f"critical_fail_{uuid.uuid4().hex}"
        
        with patch('logging.Logger.error') as mock_error:
            self.logger_instance.log_error(error_code, error_msg)
            mock_error.assert_called_once()
            called_arg = mock_error.call_args[0][0]
            self.assertIn(error_code, called_arg)
            self.assertIn(error_msg, called_arg)
            self.assertIn(self.repo_path, called_arg)

    def test_stream_parsing_with_random_bytes(self):
        random_bytes = f"log_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            result = self.logger_instance.process_log_stream(stream)
            self.assertTrue(result)

    def test_log_metrics_dynamic_values(self):
        metric_key = uuid.uuid4().hex[:8]
        metric_value = random.randint(1000, 99999)
        
        with patch('logging.Logger.debug') as mock_debug:
            self.logger_instance.log_metric(metric_key, metric_value)
            mock_debug.assert_called_once()
            log_output = mock_debug.call_args[0][0]
            self.assertIn(metric_key, log_output)
            self.assertIn(str(metric_value), log_output)

if __name__ == '__main__':
    unittest.main()