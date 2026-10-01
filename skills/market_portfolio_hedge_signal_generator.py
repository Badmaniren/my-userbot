import uuid
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.db_storage import db_storage


class MarketPortfolioHedgeSignalGenerator:
    def __init__(self, var_liquidity_core=None, stress_engine=None, db_storage=None):
        self.var_liquidity_core = var_liquidity_core
        self.stress_engine = stress_engine
        self.db_storage = db_storage

    def calculate_hedge_ratio(self, portfolio_value, var_value, liquidity_ratio, stress_loss_pct):
        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive")

        var_ratio = var_value / portfolio_value
        liquidity_penalty = 1.0 / max(liquidity_ratio, 0.05)
        raw_ratio = (var_ratio * 1.5 + stress_loss_pct * 1.2) * min(liquidity_penalty * 0.5, 1.5)
        return float(max(0.0, min(1.0, raw_ratio)))

    def select_protective_instruments(self, hedge_ratio, liquidity_ratio):
        if liquidity_ratio < 0.15:
            return ["CASH", "INVERSE_ETF"]
        elif liquidity_ratio < 0.4:
            return ["INVERSE_ETF", "PUT_OPTIONS"]
        elif hedge_ratio > 0.6:
            return ["INDEX_FUTURES", "PUT_OPTIONS"]
        else:
            return ["PUT_OPTIONS"]

    def generate_hedge_signal(self, portfolio_id, confidence_level=0.95):
        var_data = None
        if self.var_liquidity_core is not None:
            var_core_obj = self.var_liquidity_core() if isinstance(self.var_liquidity_core, type) else self.var_liquidity_core
            if hasattr(var_core_obj, "get_var_and_liquidity"):
                var_data = var_core_obj.get_var_and_liquidity(portfolio_id, confidence_level)
            elif callable(var_core_obj):
                try:
                    var_data = var_core_obj(portfolio_id=portfolio_id, confidence_level=confidence_level)
                except Exception:
                    var_data = None

        if not isinstance(var_data, dict):
            var_data = {"portfolio_value": 1000000.0, "var_value": 50000.0, "liquidity_ratio": 0.5}

        if var_data.get("portfolio_value", 0) <= 0:
            raise ValueError("Invalid portfolio value")

        stress_data = None
        if self.stress_engine is not None:
            stress_engine_obj = self.stress_engine() if isinstance(self.stress_engine, type) else self.stress_engine
            if hasattr(stress_engine_obj, "run_stress_test"):
                stress_data = stress_engine_obj.run_stress_test(portfolio_id)
            elif callable(stress_engine_obj):
                try:
                    stress_data = stress_engine_obj(portfolio_id=portfolio_id)
                except Exception:
                    stress_data = None

        if not isinstance(stress_data, dict):
            stress_data = {"stress_loss_pct": 0.1, "scenario_name": "default"}

        portfolio_value = var_data.get("portfolio_value", 1000000.0)
        var_value = var_data.get("var_value", 50000.0)
        liquidity_ratio = var_data.get("liquidity_ratio", 0.5)
        stress_loss_pct = stress_data.get("stress_loss_pct", 0.1)

        hedge_ratio = self.calculate_hedge_ratio(portfolio_value, var_value, liquidity_ratio, stress_loss_pct)
        protective_instruments = self.select_protective_instruments(hedge_ratio, liquidity_ratio)

        signal_id = f"sig_{uuid.uuid4().hex[:10]}"
        signal = {
            "signal_id": signal_id,
            "portfolio_id": portfolio_id,
            "hedge_ratio": hedge_ratio,
            "protective_instruments": protective_instruments,
            "instrument_type": protective_instruments[0] if protective_instruments else "PUT_OPTIONS"
        }

        if self.db_storage is not None:
            db_storage_obj = self.db_storage() if isinstance(self.db_storage, type) else self.db_storage
            if hasattr(db_storage_obj, "save_signal"):
                db_storage_obj.save_signal(signal)
            elif callable(db_storage_obj):
                db_storage_obj({
                    "action": "save",
                    "table": "hedge_signals",
                    "id": signal_id,
                    "data": signal
                })

        return signal


def market_portfolio_hedge_signal_generator(generator_input):
    if not isinstance(generator_input, dict):
        generator_input = {}
    portfolio_id = generator_input.get("portfolio_id")
    var_data = generator_input.get("var_data", {})
    stress_data = generator_input.get("stress_data", {})

    portfolio_value = var_data.get("portfolio_value", 100000.0)
    var_value = var_data.get("var_value", 5000.0)
    liquidity_ratio = var_data.get("liquidity_ratio", 0.5)
    stress_loss_pct = stress_data.get("stress_loss_pct", 0.15)

    if portfolio_value <= 0:
        raise ValueError("Portfolio value must be positive")

    generator = MarketPortfolioHedgeSignalGenerator()
    hedge_ratio = generator.calculate_hedge_ratio(portfolio_value, var_value, liquidity_ratio, stress_loss_pct)
    protective_instruments = generator.select_protective_instruments(hedge_ratio, liquidity_ratio)

    signal_id = f"sig_{uuid.uuid4().hex[:10]}"
    signal = {
        "signal_id": signal_id,
        "portfolio_id": portfolio_id,
        "hedge_ratio": hedge_ratio,
        "protective_instruments": protective_instruments,
        "instrument_type": protective_instruments[0] if protective_instruments else "PUT_OPTIONS"
    }

    if callable(db_storage):
        db_storage({
            "action": "save",
            "table": "hedge_signals",
            "id": signal_id,
            "data": signal
        })
    elif hasattr(db_storage, "save_signal"):
        db_storage.save_signal(signal)

    return signal
