import uuid

try:
    from skills.db_storage import db_storage
except (ImportError, AttributeError):
    db_storage = None

try:
    from skills.market_parser import market_parser
except (ImportError, AttributeError):
    market_parser = None

try:
    from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
except (ImportError, AttributeError):
    market_portfolio_scenario_simulator = None


def start_new(**kwargs):
    db = kwargs.get("db_storage") or db_storage
    parser = kwargs.get("market_parser") or market_parser
    scenario_sim = kwargs.get("market_portfolio_scenario_simulator") or market_portfolio_scenario_simulator

    if parser and hasattr(parser, "parse_stream"):
        parser.parse_stream()

    if db and hasattr(db, "save_audit_log"):
        db.save_audit_log()

    if scenario_sim and hasattr(scenario_sim, "simulate"):
        return scenario_sim.simulate()

    return {
        "factor": "",
        "inflation": 0.0,
        "interest_rate": 0.0,
        "gdp_growth": 0.0,
        "status": "evaluated"
    }


class MarketPortfolioMacroFactorEvaluator:
    def evaluate(self, portfolio_id: str, inflation: float, interest_rate: float, gdp_growth: float):
        evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
        result = {
            "evaluation_id": evaluation_id,
            "portfolio_id": portfolio_id,
            "inflation": inflation,
            "interest_rate": interest_rate,
            "gdp_growth": gdp_growth,
            "status": "evaluated"
        }
        if db_storage and hasattr(db_storage, "save_record"):
            db_storage.save_record(evaluation_id, result)
        return result


market_portfolio_macro_factor_evaluator = MarketPortfolioMacroFactorEvaluator()
