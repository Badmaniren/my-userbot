import io
import json
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_api_gateway import market_portfolio_api_gateway
from skills.market_parser import market_parser


def calculate_adv(volumes):
    if not volumes:
        raise ValueError("Volumes list cannot be empty")
    return float(sum(volumes)) / len(volumes)


def estimate_liquidation_time(position_size, adv, participation_rate=0.1):
    if adv == 0 or adv == 0.0:
        raise ZeroDivisionError("ADV cannot be zero")
    return float(position_size) / (float(adv) * float(participation_rate))


def score_liquidity_risk(days):
    days = float(days)
    if days <= 1.0:
        return "LOW"
    elif days <= 5.0:
        return "MEDIUM"
    else:
        return "HIGH"


class MarketPortfolioLiquidityAnalyzer:
    def __init__(self, db_storage=None, extractor_tool=None, market_anomaly_detector=None, **kwargs):
        self.db_storage = db_storage
        self.extractor_tool = extractor_tool
        self.market_anomaly_detector = market_anomaly_detector

    def analyze_stream(self, stream, portfolio_id=None):
        parsed = market_parser.parse_stream(stream)
        ticker = parsed.get('ticker')
        volumes = parsed.get('volumes', [])
        position_size = parsed.get('position_size', 0)

        adv = calculate_adv(volumes)
        liquidation_days = estimate_liquidation_time(position_size, adv)
        risk_score = score_liquidity_risk(liquidation_days)

        result = {
            'ticker': ticker,
            'adv': adv,
            'liquidation_days': liquidation_days,
            'risk_score': risk_score
        }

        if portfolio_id:
            result['portfolio_id'] = portfolio_id

        if self.db_storage and hasattr(self.db_storage, 'save_liquidity_metric'):
            self.db_storage.save_liquidity_metric(
                portfolio_id=portfolio_id,
                ticker=ticker,
                adv=adv,
                liquidation_days=liquidation_days,
                risk_score=risk_score
            )

        return result

    def evaluate_position_liquidity(self, ticker, position_size, portfolio_id=None):
        volumes = self._fetch_historical_volumes(ticker)
        adv = calculate_adv(volumes)
        liquidation_days = estimate_liquidation_time(position_size, adv)
        risk_score = score_liquidity_risk(liquidation_days)

        anomaly_flag = False
        if self.market_anomaly_detector and hasattr(self.market_anomaly_detector, 'check_anomaly'):
            anomaly_flag = bool(self.market_anomaly_detector.check_anomaly(ticker, position_size))

        result = {
            'ticker': ticker,
            'position_size': position_size,
            'adv': adv,
            'liquidation_days': liquidation_days,
            'risk_score': risk_score,
            'anomaly_flag': anomaly_flag
        }

        if portfolio_id:
            result['portfolio_id'] = portfolio_id

        return result

    def _fetch_historical_volumes(self, ticker):
        return [100000, 120000, 110000, 105000, 115000]


def market_portfolio_liquidity_analyzer(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    elif isinstance(payload, str):
        payload = {"portfolio_id": payload}

    portfolio_id = payload.get("portfolio_id")
    ticker = payload.get("ticker", "DEFAULT_TICKER")
    volume = payload.get("volume") or payload.get("position_size", 100000.0)

    stored = db_storage({"action": "get_position", "portfolio_id": portfolio_id, "ticker": ticker})
    if stored and isinstance(stored, dict):
        if "ticker" in stored:
            ticker = stored["ticker"]
        if "volume" in stored:
            volume = float(stored["volume"])

    analyzer = MarketPortfolioLiquidityAnalyzer()
    res = analyzer.evaluate_position_liquidity(ticker=ticker, position_size=volume, portfolio_id=portfolio_id)

    return {
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "adv": res["adv"],
        "risk_score": res["risk_score"],
        "liquidation_time_days": res["liquidation_days"],
        "status": "success"
    }
