import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import requests
from bs4 import BeautifulSoup

from skills.market_portfolio_stress_dashboard_api_v2 import start_new


class TestMarketPortfolioStressDashboardApiV2(unittest.TestCase):

    def setUp(self):
        self.random_deps = {
            "db_storage": f"db_{uuid.uuid4().hex}",
            "extractor_tool_1790087207": f"ext_1_{uuid.uuid4().hex}",
            "extractor_tool_1790102839": f"ext_2_{uuid.uuid4().hex}",
            "extractor_tool_1790262909": f"ext_3_{uuid.uuid4().hex}",
            "extractor_tool_1790621808": f"ext_4_{uuid.uuid4().hex}",
            "market_anomaly_detector": f"anomaly_{uuid.uuid4().hex}",
            "market_insider_activity_tracker": f"insider_act_{uuid.uuid4().hex}",
            "market_insider_alert_pipeline": f"insider_alert_{uuid.uuid4().hex}",
            "market_insider_anomaly_analyzer": f"insider_anom_{uuid.uuid4().hex}",
            "market_insider_anomaly_report_bridge": f"insider_bridge_{uuid.uuid4().hex}",
            "market_news_sentiment_analyzer": f"news_sent_{uuid.uuid4().hex}",
            "market_parser": f"parser_{uuid.uuid4().hex}",
            "market_portfolio_alert_dispatcher": f"port_alert_disp_{uuid.uuid4().hex}",
            "market_portfolio_alert_event_sink": f"port_alert_sink_{uuid.uuid4().hex}",
            "market_portfolio_alert_filter_router": f"port_alert_router_{uuid.uuid4().hex}",
            "market_portfolio_api_gateway": f"port_gateway_{uuid.uuid4().hex}",
            "market_portfolio_audit_alert_notifier": f"audit_notifier_{uuid.uuid4().hex}",
            "market_portfolio_audit_compliance_hub": f"audit_hub_{uuid.uuid4().hex}",
            "market_portfolio_audit_log_exporter": f"audit_exporter_{uuid.uuid4().hex}",
            "market_portfolio_autonomous_sentinel": f"sentinel_{uuid.uuid4().hex}",
            "market_portfolio_backtest_evaluator_bridge": f"backtest_bridge_{uuid.uuid4().hex}",
            "market_portfolio_backtester": f"backtester_{uuid.uuid4().hex}",
            "market_portfolio_collector_agent": f"collector_{uuid.uuid4().hex}",
            "market_portfolio_data_exporter": f"exporter_{uuid.uuid4().hex}",
            "market_portfolio_digest": f"digest_{uuid.uuid4().hex}",
            "market_portfolio_dividend_tracker": f"dividend_{uuid.uuid4().hex}",
            "market_portfolio_event_intelligence_hub": f"event_hub_{uuid.uuid4().hex}",
            "market_portfolio_execution_cost_optimizer": f"cost_opt_{uuid.uuid4().hex}",
            "market_portfolio_execution_pipeline": f"exec_pipe_{uuid.uuid4().hex}",
            "market_portfolio_integration_hub": f"integ_hub_{uuid.uuid4().hex}",
            "market_portfolio_monitor": f"monitor_{uuid.uuid4().hex}",
            "market_portfolio_performance_analytics": f"perf_anal_{uuid.uuid4().hex}",
            "market_portfolio_predictive_aggregator": f"pred_agg_{uuid.uuid4().hex}",
            "market_portfolio_scenario_simulator": f"scenario_sim_{uuid.uuid4().hex}",
            "market_portfolio_slippage_model": f"slippage_{uuid.uuid4().hex}",
            "market_portfolio_strategy_optimizer": f"strat_opt_{uuid.uuid4().hex}",
            "market_portfolio_stress_audit_visualizer": f"stress_vis_{uuid.uuid4().hex}",
            "market_portfolio_stress_monte_carlo_engine": f"monte_carlo_{uuid.uuid4().hex}",
            "market_portfolio_stress_recovery_coordinator_bridge": f"recovery_bridge_{uuid.uuid4().hex}",
            "market_portfolio_stress_reporter": f"stress_rep_{uuid.uuid4().hex}",
            "market_portfolio_stress_scenario_pipeline": f"stress_pipe_{uuid.uuid4().hex}",
            "market_portfolio_tax_calculator": f"tax_calc_{uuid.uuid4().hex}",
            "market_portfolio_telegram_command_center": f"tg_cmd_{uuid.uuid4().hex}",
            "market_portfolio_telegram_notifier": f"tg_notif_{uuid.uuid4().hex}",
            "market_portfolio_valuation": f"valuation_{uuid.uuid4().hex}",
            "market_portfolio_var_liquidity_core": f"var_liq_{uuid.uuid4().hex}",
            "market_portfolio_visualizer_v2": f"visualizer_v2_{uuid.uuid4().hex}",
            "market_portfolio_webhook_event_logger": f"wh_logger_{uuid.uuid4().hex}",
            "market_portfolio_webhook_sync": f"wh_sync_{uuid.uuid4().hex}",
            "market_report_generator": f"rep_gen_{uuid.uuid4().hex}",
            "market_sentiment_digest": f"sent_dig_{uuid.uuid4().hex}",
            "market_sentiment_risk_alert_bridge": f"sent_bridge_{uuid.uuid4().hex}",
            "market_sentiment_risk_hub": f"sent_hub_{uuid.uuid4().hex}",
            "market_sentiment_telegram_publisher": f"sent_pub_{uuid.uuid4().hex}",
            "market_telegram_pipeline": f"tg_pipe_{uuid.uuid4().hex}"
        }

    def test_start_new_initialization_and_flow(self):
        rand_token = uuid.uuid4().hex
        rand_content = f"<html><body><div id='{rand_token}'>{random.randint(1000, 9999)}</div></body></html>".encode('utf-8')
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.content = rand_content
        mock_response.text = rand_content.decode('utf-8')

        with patch("requests.get", return_value=mock_response) as mock_get:
            with patch("skills.market_portfolio_stress_dashboard_api_v2.io.BytesIO", return_value=io.BytesIO(rand_content)) as mock_io:
                result = start_new(self.random_deps)
                
                self.assertIsNotNone(result)
                mock_get.assert_called()

    def test_start_new_handles_soup_and_random_parsing(self):
        unique_class = f"class_{uuid.uuid4().hex}"
        unique_value = ''.join(random.choices(string.ascii_letters, k=12))
        html_payload = f"<html><body><span class='{unique_class}'>{unique_value}</span></body></html>"
        
        soup = BeautifulSoup(html_payload, 'html.parser')
        span_text = soup.find('span', class_=unique_class).text

        self.assertEqual(span_text, unique_value)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html_payload

        with patch("requests.post", return_value=mock_resp) as mock_post:
            res = start_new(self.random_deps)
            self.assertIsNotNone(res)

    def test_start_new_failure_resilience(self):
        with patch("requests.get", side_effect=requests.exceptions.RequestException(uuid.uuid4().hex)) as mock_get:
            try:
                start_new(self.random_deps)
            except Exception:
                pass
            mock_get.assert_called()


if __name__ == '__main__':
    unittest.main()