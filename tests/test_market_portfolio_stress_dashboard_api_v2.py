import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import requests
from bs4 import BeautifulSoup
from skills.market_portfolio_stress_dashboard_api_v2 import (
    start_new,
    market_portfolio_stress_scenario_pipeline_handler,
    market_portfolio_stress_dashboard_api_v2_handler
)

class TestMarketPortfolioStressDashboardApiV2(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        self.random_report_path = f"/var/reports/{uuid.uuid4().hex}.html"
        self.random_export_format = random.choice(["pdf", "csv", "json", "xlsx"])
        self.random_html_content = f"<html><body><h1>Stress Report {uuid.uuid4().hex}</h1></body></html>".encode('utf-8')

    @patch('skills.market_portfolio_stress_dashboard_api_v2.requests.get')
    def test_start_new_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = self.random_html_content
        mock_response.text = self.random_html_content.decode('utf-8')
        mock_get.return_value = mock_response

        random_deps_input = {uuid.uuid4().hex: random.randint(1, 100)}
        result = start_new(random_deps=random_deps_input)

        self.assertIsInstance(result, BeautifulSoup)
        self.assertIn("Stress Report", result.text)
        mock_get.assert_called_once()

    @patch('skills.market_portfolio_stress_dashboard_api_v2.requests.post')
    @patch('skills.market_portfolio_stress_dashboard_api_v2.requests.get')
    def test_start_new_request_exception_fallback_post(self, mock_get, mock_post):
        mock_get.side_effect = requests.exceptions.RequestException("Network failure")
        
        mock_response_post = MagicMock()
        mock_response_post.content = self.random_html_content
        mock_response_post.text = self.random_html_content.decode('utf-8')
        mock_post.return_value = mock_response_post

        result = start_new(random_deps=None)

        self.assertIsInstance(result, BeautifulSoup)
        mock_get.assert_called_once()
        mock_post.assert_called_once()

    def test_market_portfolio_stress_scenario_pipeline_handler_valid(self):
        payload = {"scenario_id": self.random_scenario_id, "extra": uuid.uuid4().hex}
        response = market_portfolio_stress_scenario_pipeline_handler(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "success")
        self.assertEqual(response.get("scenario_id"), self.random_scenario_id)

    @patch('skills.db_storage.db_storage_handler')
    def test_market_portfolio_stress_dashboard_api_v2_handler_execution(self, mock_db_handler):
        payload = {
            "portfolio_id": self.random_portfolio_id,
            "scenario_id": self.random_scenario_id,
            "report_path": self.random_report_path,
            "export_format": self.random_export_format
        }

        response = market_portfolio_stress_dashboard_api_v2_handler(payload)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(response.get("scenario_id"), self.random_scenario_id)
        self.assertEqual(response.get("status"), "success")
        self.assertEqual(response.get("report_path"), self.random_report_path)
        self.assertEqual(response.get("export_format"), self.random_export_format)

        mock_db_handler.assert_called_once_with({
            "query": "save_dashboard_metric",
            "portfolio_id": self.random_portfolio_id,
            "scenario_id": self.random_scenario_id,
            "report_path": self.random_report_path,
            "export_format": self.random_export_format
        })

    @patch('skills.market_portfolio_stress_dashboard_api_v2.requests.get')
    def test_start_new_bytes_io_handling(self, mock_get):
        mock_response = MagicMock()
        del mock_response.content
        mock_response.text = f"<div>{uuid.uuid4().hex}</div>"
        mock_get.return_value = mock_response

        soup = start_new(random_deps={"key": uuid.uuid4().hex})
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertTrue(len(soup.text) > 0)

if __name__ == '__main__':
    unittest.main()