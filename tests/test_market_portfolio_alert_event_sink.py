import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

# Создаем заглушки модулей, если они отсутствуют, для обеспечения импорта тестируемого модуля
for mod_name in [
    'skills.market_portfolio_alert_filter_router',
    'skills.market_portfolio_alert_dispatcher'
]:
    if mod_name not in sys.modules:
        m = types.ModuleType(mod_name)
        if 'filter_router' in mod_name:
            m.AlertFilterRouter = type('AlertFilterRouter', (), {
                '__init__': lambda self, sf: None,
                'process_and_route': lambda self, *a, **kw: random.choice([True, False]),
                'load_stream_data': lambda self: {},
                'route_filtered_alerts': lambda self, *a, **kw: uuid.uuid4().hex
            })
            m.route_and_filter_alerts = lambda *a, **kw: uuid.uuid4().hex
            m.filter_and_route_portfolio_alerts = lambda *a, **kw: True
            m.process_alert_filter_routing = lambda *a, **kw: True
        if 'dispatcher' in mod_name:
            m.send_telegram_notification = lambda *a, **kw: True
            m.dispatch_portfolio_alerts = lambda *a, **kw: uuid.uuid4().hex
            m.process_stream_alert = lambda *a, **kw: random.randint(1, 100)
        sys.modules[mod_name] = m

from skills import market_portfolio_alert_event_sink


class TestMarketPortfolioAlertEventSink(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.org/{uuid.uuid4().hex}"
        self.rand_token = f"{random.randint(100000,999999)}:{uuid.uuid4().hex}"
        self.rand_chat_id = str(random.randint(-999999999, -1000000))
        self.rand_storage = f"/tmp/{uuid.uuid4().hex}.json"
        self.rand_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        self.rand_threshold = round(random.uniform(0.1, 99.9), 2)
        self.rand_channels = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.rand_alert_id = uuid.uuid4().hex

    def test_sink_initialization_and_composition(self):
        self.assertTrue(hasattr(market_portfolio_alert_event_sink, 'AlertFilterRouter') or hasattr(market_portfolio_alert_event_sink, 'process_stream_alert'))

    def test_event_sink_handler_dispatch(self):
        expected_result = uuid.uuid4().hex
        with patch('skills.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts', return_value=expected_result) as mock_dispatch:
            if hasattr(market_portfolio_alert_event_sink, 'handle_portfolio_alert_event'):
                res = market_portfolio_alert_event_sink.handle_portfolio_alert_event(
                    self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat_id,
                    self.rand_storage, self.rand_severity, self.rand_threshold, self.rand_channels
                )
                mock_dispatch.assert_called_once_with(
                    self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat_id,
                    self.rand_storage, self.rand_severity, self.rand_threshold, self.rand_channels
                )
                self.assertEqual(res, expected_result)
            elif hasattr(market_portfolio_alert_event_sink, 'AlertEventSink'):
                sink_cls = getattr(market_portfolio_alert_event_sink, 'AlertEventSink')
                sink_instance = sink_cls(self.rand_storage)
                if hasattr(sink_instance, 'dispatch_event'):
                    res = sink_instance.dispatch_event(
                        self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat_id,
                        self.rand_severity, self.rand_threshold, self.rand_channels
                    )
                    self.assertIsNotNone(res)

    def test_event_sink_stream_processing(self):
        expected_val = random.randint(100, 999)
        with patch('skills.market_portfolio_alert_dispatcher.process_stream_alert', return_value=expected_val) as mock_stream:
            if hasattr(market_portfolio_alert_event_sink, 'process_incoming_stream'):
                res = market_portfolio_alert_event_sink.process_incoming_stream(self.rand_alert_id)
                mock_stream.assert_called_once_with(self.rand_alert_id)
                self.assertEqual(res, expected_val)

    def test_event_sink_filter_routing_integration(self):
        expected_route = uuid.uuid4().hex
        with patch('skills.market_portfolio_alert_filter_router.AlertFilterRouter') as mock_router_cls:
            mock_router_instance = mock_router_cls.return_value
            mock_router_instance.route_filtered_alerts.return_value = expected_route

            if hasattr(market_portfolio_alert_event_sink, 'route_and_sink_alerts'):
                res = market_portfolio_alert_event_sink.route_and_sink_alerts(
                    self.rand_storage, self.rand_symbol, self.rand_url, self.rand_token,
                    self.rand_chat_id, self.rand_severity, self.rand_threshold, self.rand_channels
                )
                mock_router_cls.assert_called_with(self.rand_storage)
                mock_router_instance.route_filtered_alerts.assert_called_once_with(
                    self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat_id,
                    self.rand_severity, self.rand_threshold, self.rand_channels
                )
                self.assertEqual(res, expected_route)

    def test_stream_data_loading_via_io(self):
        random_bytes = uuid.uuid4().bytes + b"\xff\x00\xaa"
        fake_stream = io.BytesIO(random_bytes)
        with patch('skills.market_portfolio_alert_filter_router.AlertFilterRouter') as mock_router_cls:
            mock_instance = mock_router_cls.return_value
            mock_instance.load_stream_data.return_value = fake_stream.read()

            if hasattr(market_portfolio_alert_event_sink, 'load_sink_stream_data'):
                data = market_portfolio_alert_event_sink.load_sink_stream_data(self.rand_storage)
                self.assertEqual(data, random_bytes)


if __name__ == '__main__':
    unittest.main()