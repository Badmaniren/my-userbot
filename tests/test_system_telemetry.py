import unittest
from unittest.mock import patch, MagicMock
import io

from skills.system_telemetry import start_new


class TestSystemTelemetryStartNew(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_start_new_success(self):
        with patch('skills.system_telemetry.some_dependency') as mock_dep:
            mock_dep.return_value = True
            result = start_new()
            self.assertTrue(result)

    def test_start_new_failure(self):
        with patch('skills.system_telemetry.some_dependency') as mock_dep:
            mock_dep.return_value = False
            result = start_new()
            self.assertFalse(result)

    def test_start_new_raises_exception(self):
        with patch('skills.system_telemetry.some_dependency') as mock_dep:
            mock_dep.side_effect = Exception("Telemetry system failure")
            with self.assertRaises(Exception):
                start_new()

    def test_start_new_with_stream_data(self):
        stream_mock = io.BytesIO(b'TELEMETRY_DATA_OK')
        with patch('skills.system_telemetry.process_stream_data') as mock_process:
            mock_process.return_value = True
            result = start_new(stream=stream_mock)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()