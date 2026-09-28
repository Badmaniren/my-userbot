import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
import datetime
import sys

from skills.market_portfolio_hedge_engine import MarketPortfolioHedgeEngine


class TestMarketPortfolioHedgeEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.instrument = f"INSTR_{uuid.uuid4().hex[:6].upper()}"
        self.strategy_id = f"STRAT_{uuid.uuid4().hex[:6]}"
        self.tail_risk_analyzer = MagicMock()
        self.db_storage = MagicMock()
        self.engine = MarketPortfolioHedgeEngine(
            tail_risk_analyzer=self.tail_risk_analyzer,
            portfolio_id=self.portfolio_id,
            db_storage=self.db_storage
        )

    def test_init_properties(self):
        rnd_pid = str(uuid.uuid4())
        analyzer = MagicMock()
        storage = MagicMock()
        eng = MarketPortfolioHedgeEngine(tail_risk_analyzer=analyzer, portfolio_id=rnd_pid, db_storage=storage)
        self.assertEqual(eng.tail_risk_analyzer, analyzer)
        self.assertEqual(eng.portfolio_id, rnd_pid)
        self.assertEqual(eng.db_storage, storage)

    def test_fetch_instrument_beta(self):
        beta = self.engine._fetch_instrument_beta(self.instrument)
        self.assertEqual(beta, 1.0)

    def test_compute_hedge_delta(self):
        var_val = random.uniform(100.0, 5000.0)
        cvar_val = random.uniform(500.0, 10000.0)
        self.tail_risk_analyzer.calculate_var.return_value = var_val
        self.tail_risk_analyzer.calculate_cvar.return_value = cvar_val

        delta = self.engine.compute_hedge_delta(self.instrument)
        expected = (var_val + cvar_val) * 1.0
        self.assertEqual(delta, expected)
        self.tail_risk_analyzer.calculate_var.assert_called_once_with(self.portfolio_id)
        self.tail_risk_analyzer.calculate_cvar.assert_called_once_with(self.portfolio_id)

    def test_generate_hedge_orders(self):
        var_val = random.uniform(10.0, 100.0)
        cvar_val = random.uniform(20.0, 200.0)
        self.tail_risk_analyzer.calculate_var.return_value = var_val
        self.tail_risk_analyzer.calculate_cvar.return_value = cvar_val

        order = self.engine.generate_hedge_orders(self.instrument, self.strategy_id)
        self.assertEqual(order['instrument'], self.instrument)
        self.assertEqual(order['portfolio_id'], self.portfolio_id)
        self.assertEqual(order['required_delta'], float(var_val + cvar_val))
        self.assertEqual(order['strategy_tag'], self.strategy_id)
        self.assertIn('timestamp', order)

    def test_consume_external_risk_feed(self):
        url = f"https://{uuid.uuid4().hex}.com/feed"
        random_bytes = uuid.uuid4().hex.encode('utf-8')

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(random_bytes)
            mock_get.return_value = mock_response

            result = self.engine.consume_external_risk_feed(url)
            mock_get.assert_called_once_with(url, stream=True)
            self.assertEqual(result, random_bytes.decode('utf-8'))

    def test_write_audit_log(self):
        file_path = f"{uuid.uuid4().hex}.log"
        message = f"MSG_{uuid.uuid4().hex}"

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.engine.write_audit_log(file_path, message)
            mock_open.assert_called_once_with(file_path, 'a', encoding='utf-8')
            mock_file.write.assert_called_once()
            written_arg = mock_file.write.call_args[0][0]
            self.assertIn(message, written_arg)

    def test_calculate_hedge_volume_defaults(self):
        risk_data = {}
        corr = random.uniform(0.1, 2.0)
        res = self.engine.calculate_hedge_volume(self.portfolio_id, risk_data, corr)

        expected_volume = (1000.0 + 5000.0) * corr
        self.assertEqual(res['hedge_volume'], float(expected_volume))
        self.assertEqual(res['instrument_id'], "DEFAULT_HEDGE_INSTRUMENT")
        self.assertEqual(res['portfolio_id'], self.portfolio_id)

    def test_calculate_hedge_volume_custom(self):
        var_v = random.uniform(10.0, 500.0)
        cvar_v = random.uniform(50.0, 1500.0)
        risk_data = {"var_95": var_v, "cvar_99": cvar_v}
        corr = random.uniform(0.5, 3.0)

        res = self.engine.calculate_hedge_volume(self.portfolio_id, risk_data, corr)
        expected_volume = (var_v + cvar_v) * corr
        self.assertEqual(res['hedge_volume'], float(expected_volume))

    def test_generate_report(self):
        run_id = f"RUN_{uuid.uuid4().hex}"
        path = f"{uuid.uuid4().hex}.json"

        with patch('json.dump') as mock_json_dump, patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            self.engine.generate_report(run_id, path)
            mock_open.assert_called_once_with(path, 'w', encoding='utf-8')
            mock_json_dump.assert_called_once()
            dumped_data = mock_json_dump.call_args[0][0]
            self.assertEqual(dumped_data["run_id"], run_id)
            self.assertEqual(dumped_data["status"], "success")
            self.assertIn("timestamp", dumped_data)