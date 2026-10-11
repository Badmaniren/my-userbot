import io
import math
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.market_portfolio_slippage_model import (
    MarketPortfolioSlippageModel,
    OrderExecutionParameters,
    SlippageCalculationError,
)


def _rnd_str(prefix="str_"):
    return f"{prefix}{uuid.uuid4().hex}"


def _rnd_ticker():
    letters = random.choices(string.ascii_uppercase, k=random.randint(3, 5))
    return "".join(letters) + "_" + uuid.uuid4().hex[:4]


class TestMarketPortfolioSlippageModelInquisition(unittest.TestCase):
    def setUp(self):
        self.kwargs = {
            f"kw_{uuid.uuid4().hex[:6]}": uuid.uuid4().hex
            for _ in range(random.randint(2, 4))
        }
        self.model = MarketPortfolioSlippageModel(**self.kwargs)

    def test_init_and_kwargs_dynamic_assignment(self):
        custom_key = f"attr_{uuid.uuid4().hex}"
        custom_val = uuid.uuid4().hex
        dummy_db = MagicMock()
        model = MarketPortfolioSlippageModel(
            **{custom_key: custom_val, "db_storage": dummy_db}
        )
        self.assertEqual(getattr(model, custom_key), custom_val)
        self.assertEqual(model.db_storage, dummy_db)
        self.assertEqual(model._execution_logs, {})

    def test_calculate_slippage_invalid_parameters_raises(self):
        # 1. Пустой тикер
        bad_order_1 = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker="",
            volume=random.uniform(10.0, 1000.0),
            volatility=random.uniform(0.01, 0.5),
        )
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(bad_order_1)

        # 2. Неположительный объем
        bad_order_2 = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=_rnd_ticker(),
            volume=random.choice([0.0, -random.uniform(0.1, 500.0)]),
            volatility=random.uniform(0.01, 0.5),
        )
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(bad_order_2)

        # 3. Неположительная волатильность
        bad_order_3 = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=_rnd_ticker(),
            volume=random.uniform(10.0, 1000.0),
            volatility=random.choice([0.0, -random.uniform(0.01, 0.5)]),
        )
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(bad_order_3)

    def test_calculate_slippage_without_parser(self):
        volume = round(random.uniform(100.0, 50000.0), 4)
        volatility = round(random.uniform(0.05, 0.95), 4)
        order = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=_rnd_ticker(),
            volume=volume,
            volatility=volatility,
        )
        expected = round(volume * volatility * 0.0001 * 1.0, 6)
        result = self.model.calculate_slippage(order)
        self.assertAlmostEqual(result, expected, places=6)

    def test_calculate_slippage_with_parser_dynamic_liquidity(self):
        mock_parser = MagicMock()
        ticker = _rnd_ticker()
        volume = round(random.uniform(500.0, 2000.0), 2)
        volatility = round(random.uniform(0.1, 0.8), 3)

        # Случай 1: парсер возвращает словарь с total_depth
        total_depth = round(random.uniform(100.0, 10000.0), 2)
        mock_parser.parse_market_depth.return_value = {"total_depth": total_depth}

        model = MarketPortfolioSlippageModel(market_parser=mock_parser)
        order = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=volume,
            volatility=volatility,
        )

        expected_depth_factor = min(2.0, volume / max(total_depth, 1.0))
        expected_res = round(volume * volatility * 0.0001 * expected_depth_factor, 6)

        result = model.calculate_slippage(order)
        mock_parser.parse_market_depth.assert_called_once_with(ticker)
        self.assertAlmostEqual(result, expected_res, places=6)

        # Случай 2: парсер возвращает пустой/некорректный ответ (fall back на 1.0)
        mock_parser.reset_mock()
        mock_parser.parse_market_depth.return_value = None
        fallback_res = model.calculate_slippage(order)
        self.assertAlmostEqual(fallback_res, round(volume * volatility * 0.0001 * 1.0, 6), places=6)

    def test_fetch_external_liquidity_profile(self):
        ticker = _rnd_ticker()
        volume = round(random.uniform(100.0, 5000.0), 2)
        fake_payload = uuid.uuid4().hex.encode("utf-8")
        stream_bytes = io.BytesIO(fake_payload)

        mock_response = MagicMock()
        mock_response.raw = stream_bytes

        mock_gateway = MagicMock()
        model = MarketPortfolioSlippageModel(market_portfolio_api_gateway=mock_gateway)

        with patch("skills.market_portfolio_slippage_model.requests.get") as mock_get:
            mock_get.return_value = mock_response

            raw_stream = model.fetch_external_liquidity_profile(ticker, volume)

            mock_get.assert_called_once_with(f"https://api.example.com/liquidity/{ticker}?volume={volume}")
            mock_gateway.log_request.assert_called_once_with(ticker, volume)
            self.assertEqual(raw_stream.read(), fake_payload)

    def test_estimate_market_impact_with_anomalies_and_alert(self):
        ticker = _rnd_ticker()
        volume = round(random.uniform(500.0, 10000.0), 2)
        volatility = round(random.uniform(0.1, 0.5), 3)
        multiplier = round(random.uniform(1.2, 3.5), 2)
        anomaly_payload = {"multiplier": multiplier, "anomaly_id": uuid.uuid4().hex}

        mock_detector = MagicMock()
        mock_detector.detect.return_value = anomaly_payload

        mock_dispatcher = MagicMock()

        model = MarketPortfolioSlippageModel(
            market_anomaly_detector=mock_detector,
            alert_dispatcher=mock_dispatcher,
        )

        order = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=ticker,
            volume=volume,
            volatility=volatility,
        )

        impact = model.estimate_market_impact(order)
        mock_detector.detect.assert_called_once_with(ticker)
        mock_dispatcher.dispatch.assert_called_once_with(anomaly_payload)
        expected_impact = float(volume * volatility * 0.00005 * multiplier)
        self.assertAlmostEqual(impact, expected_impact, places=6)

    def test_estimate_market_impact_default_without_detector(self):
        volume = round(random.uniform(100.0, 1000.0), 2)
        volatility = round(random.uniform(0.1, 0.3), 3)
        order = OrderExecutionParameters(
            order_id=uuid.uuid4().hex,
            ticker=_rnd_ticker(),
            volume=volume,
            volatility=volatility,
        )
        impact = self.model.estimate_market_impact(order)
        expected_impact = float(volume * volatility * 0.00005 * 1.0)
        self.assertAlmostEqual(impact, expected_impact, places=6)

    def test_simulate_stress_slippage(self):
        ticker = _rnd_ticker()
        volume = round(random.uniform(1000.0, 50000.0), 2)
        scenario_name = _rnd_str("stress_scenario_")
        stress_mult = round(random.uniform(1.5, 4.0), 2)

        mock_pipeline = MagicMock()
        mock_pipeline.run_simulation.return_value = {"stress_multiplier": stress_mult}

        model = MarketPortfolioSlippageModel(market_portfolio_stress_scenario_pipeline=mock_pipeline)

        result = model.simulate_stress_slippage(ticker, volume, scenario_name)

        mock_pipeline.run_simulation.assert_called_once_with(scenario_name)
        self.assertEqual(result["scenario"], scenario_name)
        self.assertEqual(result["stress_multiplier"], stress_mult)
        expected_adjusted = round(volume * 0.2 * 0.0001 * stress_mult, 6)
        self.assertEqual(result["adjusted_slippage"], expected_adjusted)

    def test_simulate_order_execution_buy_and_sell(self):
        # Тест BUY
        order_buy = {
            "order_id": uuid.uuid4().hex,
            "symbol": _rnd_ticker(),
            "side": "BUY",
            "quantity": random.uniform(50.0, 500.0),
            "price": random.uniform(10.0, 200.0),
        }
        ctx_buy = {
            "adv": random.uniform(10000.0, 100000.0),
            "volatility": random.uniform(0.1, 0.4),
            "spread_bps": random.uniform(2.0, 15.0),
        }

        res_buy = self.model.simulate_order_execution(order_buy, ctx_buy)
        self.assertEqual(res_buy["order_id"], order_buy["order_id"])
        self.assertEqual(res_buy["status"], "FILLED")
        self.assertGreater(res_buy["executed_price"], order_buy["price"])

        # Проверка математики BUY
        p_rate = order_buy["quantity"] / ctx_buy["adv"]
        impact = order_buy["price"] * ctx_buy["volatility"] * (p_rate ** 0.5) * 0.1
        half_spread = order_buy["price"] * (ctx_buy["spread_bps"] / 10000.0)
        slippage_val = half_spread + impact
        self.assertAlmostEqual(res_buy["executed_price"], round(order_buy["price"] + slippage_val, 4), places=4)
        self.assertAlmostEqual(res_buy["realized_cost"], round((order_buy["price"] + slippage_val) * order_buy["quantity"], 2), places=2)

        # Тест SELL
        order_sell = {
            "order_id": uuid.uuid4().hex,
            "symbol": _rnd_ticker(),
            "side": "SELL",
            "quantity": random.uniform(50.0, 500.0),
            "price": random.uniform(10.0, 200.0),
        }
        res_sell = self.model.simulate_order_execution(order_sell, ctx_buy)
        self.assertLess(res_sell["executed_price"], order_sell["price"])

    def test_simulate_batch(self):
        sym_1, sym_2 = _rnd_ticker(), _rnd_ticker()
        batch = [
            {"order_id": uuid.uuid4().hex, "symbol": sym_1, "side": "BUY", "quantity": 100, "price": 50.0},
            {"order_id": uuid.uuid4().hex, "symbol": sym_2, "side": "SELL", "quantity": 200, "price": 100.0},
        ]
        contexts = {
            sym_1: {"adv": 50000, "volatility": 0.15, "spread_bps": 4.0}
            # sym_2 намеренно отсутствует для проверки fallback контекста
        }

        results = self.model.simulate_batch(batch, contexts)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["order_id"], batch[0]["order_id"])
        self.assertEqual(results[1]["order_id"], batch[1]["order_id"])
        self.assertEqual(results[0]["symbol"], sym_1)
        self.assertEqual(results[1]["symbol"], sym_2)

    def test_persist_and_get_execution_logs(self):
        sim_id = uuid.uuid4().hex
        dummy_logs = [
            {"execution_id": uuid.uuid4().hex, "price": round(random.uniform(10, 100), 2)}
            for _ in range(random.randint(2, 5))
        ]
        mock_storage = MagicMock()

        # Сохранение логов
        persisted = self.model.persist_execution_logs(sim_id, dummy_logs, mock_storage)
        self.assertTrue(persisted)
        mock_storage.save_logs.assert_called_once_with(sim_id, dummy_logs)

        # Получение из внутреннего кэша (self._execution_logs)
        cached_logs = self.model.get_execution_logs(sim_id, mock_storage)
        self.assertEqual(cached_logs, dummy_logs)

        # Получение из внешнего хранилища, если в кэше нет
        other_sim_id = uuid.uuid4().hex
        storage_logs = [{"execution_id": uuid.uuid4().hex}]
        mock_storage.get_logs.return_value = storage_logs
        fetched_logs = self.model.get_execution_logs(other_sim_id, mock_storage)
        mock_storage.get_logs.assert_called_once_with(other_sim_id)
        self.assertEqual(fetched_logs, storage_logs)

        # Если нигде нет
        mock_storage_empty = MagicMock()
        mock_storage_empty.get_logs.return_value = []
        not_found_logs = self.model.get_execution_logs(uuid.uuid4().hex, mock_storage_empty)
        self.assertEqual(not_found_logs, [])


if __name__ == "__main__":
    unittest.main()