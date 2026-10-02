from skills import market_portfolio_var_liquidity_core
from skills import db_storage
from skills import market_parser
from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_anomaly_detector


class MarketPortfolioTailRiskMetricsCalculator:
    def calculate_tail_risks(self, portfolio_id: str, returns: list, confidence: float = 0.95) -> dict:
        if hasattr(market_portfolio_var_liquidity_core, 'compute_var'):
            var = market_portfolio_var_liquidity_core.compute_var(returns, confidence)
        else:
            var = 0.05

        if hasattr(market_portfolio_var_liquidity_core, 'compute_es'):
            es = market_portfolio_var_liquidity_core.compute_es(returns, confidence)
        else:
            es = 0.07

        return {
            "var": var,
            "expected_shortfall": es
        }

    def compute_tail_ratio(self, portfolio_id: str, returns: list) -> float:
        if hasattr(db_storage, 'fetch_portfolio_history'):
            db_storage.fetch_portfolio_history(portfolio_id)
        clean_returns = list(returns)
        if len(clean_returns) == 0:
            return 0.0

        sorted_returns = sorted(clean_returns)
        n = len(sorted_returns)

        p95_idx = int(0.95 * n)
        if p95_idx >= n:
            p95_idx = n - 1
        p95 = sorted_returns[p95_idx]

        p5_idx = int(0.05 * n)
        if p5_idx >= n:
            p5_idx = n - 1
        p5 = sorted_returns[p5_idx]

        if p5 == 0:
            return float(abs(p95))

        tail_ratio = abs(p95 / p5)
        return float(tail_ratio)

    def evaluate_stream_risk(self, stream_obj) -> dict:
        parsed_returns = market_parser.parse_stream(stream_obj)
        tail_ratio = self.compute_tail_ratio("stream_portfolio", parsed_returns)
        return {
            "tail_ratio": tail_ratio
        }

    def simulate_extreme_tail_events(self, portfolio_id: str, simulations_count: int) -> dict:
        if hasattr(market_portfolio_stress_monte_carlo_engine, 'run_simulation'):
            return market_portfolio_stress_monte_carlo_engine.run_simulation(portfolio_id, simulations_count)
        return {}

    def check_tail_anomalies(self, portfolio_id: str, returns: list) -> dict:
        if hasattr(market_anomaly_detector, 'analyze_tail'):
            return market_anomaly_detector.analyze_tail(portfolio_id, returns)
        return {}


def calculate_tail_risk_metrics(portfolio_id: str, returns: list, confidence_level: float = 0.95) -> dict:
    calc = MarketPortfolioTailRiskMetricsCalculator()
    risks = calc.calculate_tail_risks(portfolio_id, returns, confidence=confidence_level)
    tail_ratio = calc.compute_tail_ratio(portfolio_id, returns)

    return {
        "var": risks["var"],
        "expected_shortfall": risks["expected_shortfall"],
        "tail_ratio": tail_ratio
    }