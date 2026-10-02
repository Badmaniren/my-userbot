import os

try:
    import requests
except ImportError:
    requests = None

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

try:
    from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
except ImportError:
    market_portfolio_collector_agent = None

try:
    from skills.market_portfolio_valuation import market_portfolio_valuation
except ImportError:
    market_portfolio_valuation = None


class MarketPortfolioMacroLiquidityAnalyzer:
    """Класс для оценки макроэкономических факторов ликвидности портфеля."""

    def __init__(self, default_threshold=0.0, default_macro_factor=1.0):
        self.default_threshold = default_threshold
        self.default_macro_factor = default_macro_factor

    def evaluate_liquidity(self, data=None):
        return market_portfolio_macro_liquidity_analyzer(data)

    def analyze(self, data=None):
        return self.evaluate_liquidity(data)


def start_new(*args, **kwargs):
    """Выполнение основного пайплайна модуля макро-ликвидности портфеля."""
    dependencies = args[0] if args and isinstance(args[0], dict) else kwargs

    if isinstance(dependencies, dict):
        for key, value in dependencies.items():
            if key.startswith("extractor_tool_") and callable(value):
                value()

        anomaly = dependencies.get("market_anomaly_detector")
        if callable(anomaly):
            anomaly()

    stream = kwargs.get("stream") or kwargs.get("input_stream")
    if stream and hasattr(stream, "read"):
        stream.read()

    return {"status": "success"}


def market_portfolio_macro_liquidity_analyzer(data=None, *args, **kwargs):
    """Интеграционный аналилизатор макроликвидности портфеля."""
    if not isinstance(data, dict):
        data = kwargs if kwargs else {}

    portfolio_id = data.get("portfolio_id", "default_portfolio")
    liquidity_threshold = data.get("liquidity_threshold", 0.0)
    macro_factor = data.get("macro_factor", 1.0)
    valuation_ref = data.get("valuation_ref")

    base_score = 50000.0
    if isinstance(valuation_ref, (int, float)):
        base_score = float(valuation_ref)
    elif isinstance(valuation_ref, dict):
        base_score = float(valuation_ref.get("valuation", 50000.0))

    try:
        mf = float(macro_factor)
    except (TypeError, ValueError):
        mf = 1.0

    liquidity_score = base_score * mf

    try:
        lt = float(liquidity_threshold)
    except (TypeError, ValueError):
        lt = 0.0

    return {
        "portfolio_id": portfolio_id,
        "liquidity_threshold": liquidity_threshold,
        "macro_factor": macro_factor,
        "liquidity_score": liquidity_score,
        "is_liquid": liquidity_score >= lt,
        "status": "success"
    }
