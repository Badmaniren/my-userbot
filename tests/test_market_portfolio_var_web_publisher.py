import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.market_portfolio_var_web_publisher import (
    VarPublisherException,
    MarketPortfolioVarWebPublisher,
    market_portfolio_var_web_publisher
)

class TestMarketPortfolioVarWebPublisher(unittest.TestCase):

    def setUp(self):
        self.rand_str = uuid.uuid4().hex
        self.webhook_url = f"https://{self.rand_str}.com/webhook"
        self.api_token = f"token_{uuid.uuid4().hex}"
        self.publisher = MarketPortfolioVarWebPublisher(webhook_url=self.webhook_url, api_token=self.api_token)

    def test_get_headers_with_token(self):
        headers = self.publisher._get_headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], f"Bearer {self.api_token}")

    def test_get_headers_without_token(self):
        pub_no_token = MarketPortfolioVarWebPublisher(webhook_url=self.webhook_url)
        headers = pub_no_token._get_headers()
        self.assertEqual(headers, {})

    def test_publish_var_report_success(self):
        payload_key = uuid.uuid4().hex
        payload_val = uuid.uuid4().hex
        payload = {payload_key: payload_val}

        expected_response_key = uuid.uuid4().hex
        expected_response_val = uuid.uuid4().hex
        mock_response_data = {expected_response_key: expected_response_val}

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            result = self.publisher.publish_var_report(payload)

            mock_post.assert_called_once_with(
                self.webhook_url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            self.assertEqual(result, mock_response_data)

    def test_publish_var_report_http_error(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            http_err = requests.exceptions.HTTPError(uuid.uuid4().hex)
            mock_resp.raise_for_status.side_effect = http_err
            mock_post.return_value = mock_resp

            with self.assertRaises(VarPublisherException) as ctx:
                self.publisher.publish_var_report(payload)
            self.assertIn("HTTP error occurred", str(ctx.exception))

    def test_publish_var_report_request_exception(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            req_err = requests.exceptions.RequestException(uuid.uuid4().hex)
            mock_post.side_effect = req_err

            with self.assertRaises(VarPublisherException) as ctx:
                self.publisher.publish_var_report(payload)
            self.assertIn("Failed to publish VaR report", str(ctx.exception))

    def test_stream_risk_metrics_with_read_attribute(self):
        random_bytes = uuid.uuid4().bytes
        stream_data = io.BytesIO(random_bytes)

        expected_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_res
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            result = self.publisher.stream_risk_metrics(stream_data)

            mock_post.assert_called_once_with(
                self.webhook_url,
                data=random_bytes,
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            self.assertEqual(result, expected_res)

    def test_stream_risk_metrics_without_read_attribute(self):
        raw_data = uuid.uuid4().hex
        expected_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_res
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            result = self.publisher.stream_risk_metrics(raw_data)

            mock_post.assert_called_once_with(
                self.webhook_url,
                data=raw_data,
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            self.assertEqual(result, expected_res)

    def test_stream_risk_metrics_exception(self):
        stream_data = uuid.uuid4().hex

        with patch("skills.market_portfolio_var_web_publisher.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            with self.assertRaises(VarPublisherException) as ctx:
                self.publisher.stream_risk_metrics(stream_data)
            self.assertIn("Failed to stream risk metrics", str(ctx.exception))

    def test_verify_webhook_connection_success(self):
        health_url = f"{self.webhook_url}/health"
        response_text = uuid.uuid4().hex

        with patch("skills.market_portfolio_var_web_publisher.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = response_text
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            is_valid = self.publisher.verify_webhook_connection()

            mock_get.assert_called_once_with(
                health_url,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10
            )
            self.assertTrue(is_valid)

    def test_verify_webhook_connection_empty_text(self):
        health_url = f"{self.webhook_url}/health"

        with patch("skills.market_portfolio_var_web_publisher.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.text = ""
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            is_valid = self.publisher.verify_webhook_connection()
            self.assertFalse(is_valid)

    def test_verify_webhook_connection_failure(self):
        health_url = f"{self.webhook_url}/health"

        with patch("skills.market_portfolio_var_web_publisher.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            is_valid = self.publisher.verify_webhook_connection()
            self.assertFalse(is_valid)

    def test_wrapper_function_market_portfolio_var_web_publisher(self):
        portfolio_id = uuid.uuid4().hex
        webhook_url = f"https://{uuid.uuid4().hex}.net/hook"
        var_data = {uuid.uuid4().hex: random.random()}
        api_token = uuid.uuid4().hex

        published_id_val = uuid.uuid4().hex
        status_val = uuid.uuid4().hex

        mock_return = {
            "id": published_id_val,
            "status": status_val
        }

        with patch("skills.market_portfolio_var_web_publisher.MarketPortfolioVarWebPublisher.publish_var_report") as mock_publish:
            mock_publish.return_value = mock_return

            res = market_portfolio_var_web_publisher(
                portfolio_id=portfolio_id,
                webhook_url=webhook_url,
                var_data=var_data,
                api_token=api_token
            )

            mock_publish.assert_called_once_with({
                "portfolio_id": portfolio_id,
                "var_data": var_data
            })

            self.assertEqual(res["published_id"], published_id_val)
            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["target_webhook"], webhook_url)
            self.assertEqual(res["status"], status_val)

    def test_wrapper_function_defaults_fallback(self):
        portfolio_id = uuid.uuid4().hex
        webhook_url = f"https://{uuid.uuid4().hex}.net/hook"
        var_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_var_web_publisher.MarketPortfolioVarWebPublisher.publish_var_report") as mock_publish:
            mock_publish.return_value = {}

            res = market_portfolio_var_web_publisher(
                portfolio_id=portfolio_id,
                webhook_url=webhook_url,
                var_data=var_data
            )

            self.assertEqual(res["published_id"], portfolio_id)
            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["target_webhook"], webhook_url)
            self.assertEqual(res["status"], "success")