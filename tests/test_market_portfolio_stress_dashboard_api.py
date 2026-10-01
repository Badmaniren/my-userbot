import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string
from skills.market_portfolio_stress_dashboard_api import start_new

class TestMarketPortfolioStressDashboardApiStartNew(unittest.TestCase):

    def test_start_new_success_execution_path(self):
        rand_sim_name = uuid.uuid4().hex
        rand_url = f"http://{uuid.uuid4().hex}.local"
        rand_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        
        sim_mock = MagicMock()
        sim_mock.simulate = MagicMock(return_value=rand_sim_name)

        rg_mock = MagicMock()
        rg_mock.get = MagicMock(return_value=True)

        stream_mock = MagicMock()
        stream_mock.read = MagicMock(return_value=rand_stream_data)

        db_mock = MagicMock()
        db_mock.fetch_stream = MagicMock(return_value=stream_mock)

        det_mock = MagicMock()
        det_mock.detect = MagicMock(return_value=True)

        dependencies = {
            "market_portfolio_scenario_simulator": sim_mock,
            "market_portfolio_api_gateway": rg_mock,
            "db_storage": db_mock,
            "market_anomaly_detector": det_mock
        }

        result = start_new(dependencies)

        sim_mock.simulate.assert_called_once()
        rg_mock.get.assert_called_once_with("http://localhost")
        db_mock.fetch_stream.assert_called_once()
        stream_mock.read.assert_called_once()
        det_mock.detect.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_start_new_missing_optional_dependencies(self):
        rand_url = f"http://{uuid.uuid4().hex}.test"
        rg_mock = MagicMock()
        
        dependencies = {
            "market_portfolio_api_gateway": rg_mock
        }

        result = start_new(dependencies)

        rg_mock.get.assert_called_once_with("http://localhost")
        self.assertEqual(result, {"status": "success"})

    def test_start_new_db_stream_none(self):
        sim_mock = MagicMock()
        rg_mock = MagicMock()
        
        db_mock = MagicMock()
        db_mock.fetch_stream = MagicMock(return_value=None)

        det_mock = MagicMock()

        dependencies = {
            "market_portfolio_scenario_simulator": sim_mock,
            "market_portfolio_api_gateway": rg_mock,
            "db_storage": db_mock,
            "market_anomaly_detector": det_mock
        }

        result = start_new(dependencies)

        sim_mock.simulate.assert_called_once()
        rg_mock.get.assert_called_once_with("http://localhost")
        db_mock.fetch_stream.assert_called_once()
        det_mock.detect.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_start_new_requests_fallback(self):
        rand_stream_data = io.BytesIO(b"<html><body><h1>" + uuid.uuid4().hex.encode() + b"</h1></body></html>")
        db_mock = MagicMock()
        db_mock.fetch_stream = MagicMock(return_value=rand_stream_data)

        dependencies = {
            "db_storage": db_mock
        }

        with patch("requests.get") as mock_requests_get:
            result = start_new(dependencies)
            mock_requests_get.assert_called_once_with("http://localhost")
            self.assertEqual(result, {"status": "success"})

    def test_start_new_sim_without_simulate_attr(self):
        sim_mock = object()
        rg_mock = MagicMock()

        dependencies = {
            "market_portfolio_scenario_simulator": sim_mock,
            "market_portfolio_api_gateway": rg_mock
        }

        result = start_new(dependencies)
        rg_mock.get.assert_called_once_with("http://localhost")
        self.assertEqual(result, {"status": "success"})

    def test_start_new_det_without_detect_attr(self):
        det_mock = object()
        rg_mock = MagicMock()

        dependencies = {
            "market_anomaly_detector": det_mock,
            "market_portfolio_api_gateway": rg_mock
        }

        result = start_new(dependencies)
        rg_mock.get.assert_called_once_with("http://localhost")
        self.assertEqual(result, {"status": "success"})

if __name__ == "__main__":
    unittest.main()