from skills.db_storage import DbStorage, db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core


class MacroLiquidityGate:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.db_storage = kwargs.get("db_storage")
        self.extractor_1 = kwargs.get("extractor_tool_1790087207")
        self.var_liquidity_core = kwargs.get("market_portfolio_var_liquidity_core")
        self.audit_notifier = kwargs.get("market_portfolio_audit_alert_notifier")
        self.parser = kwargs.get("market_parser")
        self.liquidity_scenario = kwargs.get("market_portfolio_liquidity_scenario_analyzer")
        self.scenario_simulator = kwargs.get("market_portfolio_scenario_simulator")

    def aggregate_macro_liquidity(self, portfolio_id: str) -> dict:
        try:
            extracted_data = {}
            if self.extractor_1 and hasattr(self.extractor_1, "extract"):
                extracted_data = self.extractor_1.extract(portfolio_id)

            var_score = 0.0
            if self.var_liquidity_core:
                core = self.var_liquidity_core() if isinstance(self.var_liquidity_core, type) else self.var_liquidity_core
                if hasattr(core, "calculate"):
                    var_score = core.calculate(portfolio_id)
                elif hasattr(core, "calculate_var_and_liquidity"):
                    res = core.calculate_var_and_liquidity(portfolio_id, 0.95)
                    if isinstance(res, dict):
                        var_score = res.get("var_value", 0.0)
                    elif isinstance(res, (int, float)):
                        var_score = float(res)

            score = sum(v for v in extracted_data.values() if isinstance(v, (int, float))) + var_score

            result = {
                "portfolio_id": portfolio_id,
                "macro_liquidity_score": score,
                "details": extracted_data
            }

            if self.db_storage and hasattr(self.db_storage, "save"):
                self.db_storage.save(result)

            return result
        except Exception as e:
            if self.audit_notifier and hasattr(self.audit_notifier, "notify_error"):
                self.audit_notifier.notify_error(str(e))
            raise

    def process_external_stream(self, stream_id: str) -> dict:
        import requests
        response = requests.get(f"http://example.com/stream/{stream_id}")
        parsed = {}
        if self.parser and hasattr(self.parser, "parse_stream"):
            parsed = self.parser.parse_stream(response.raw)
        return {
            "status": "success",
            "stream_id": stream_id,
            "parsed": parsed
        }

    def run_liquidity_scenario(self, scenario_id: str, shock: float) -> dict:
        res = {}
        if self.liquidity_scenario and hasattr(self.liquidity_scenario, "simulate"):
            res = self.liquidity_scenario.simulate(scenario_id, shock)
        if self.scenario_simulator and hasattr(self.scenario_simulator, "record"):
            self.scenario_simulator.record(res)
        return res


def market_portfolio_macro_liquidity_gate(input_data: dict) -> dict:
    portfolio_id = input_data.get("portfolio_id")
    liquidity_data = input_data.get("liquidity_data", {})
    macro_factor = input_data.get("macro_factor")

    base_val = 0.0
    if isinstance(liquidity_data, dict):
        base_val = liquidity_data.get("base_liquidity", 0.0)

    aggregated_score = base_val + (macro_factor if isinstance(macro_factor, (int, float)) else 0.0)

    output = {
        "portfolio_id": portfolio_id,
        "macro_factor": macro_factor,
        "aggregated_score": aggregated_score,
        "liquidity_data": liquidity_data
    }

    return output
