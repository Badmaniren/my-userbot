import uuid
import io

class MacroShockSimulator:
    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None, market_portfolio_alert_dispatcher=None):
        self.db_storage = db_storage
        self.scenario_sim = market_portfolio_scenario_simulator
        self.alert_dispatcher = market_portfolio_alert_dispatcher

    def simulate_shock(self, portfolio_id, shock_type, shock_magnitude):
        if self.db_storage:
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")

        simulation_result = {}
        if self.scenario_sim:
            simulation_result = self.scenario_sim.run_scenario(portfolio_id, shock_type, shock_magnitude)

        event_id = uuid.uuid4()

        result = {
            "event_id": event_id.hex,
            "portfolio_id": portfolio_id,
            "shock_type": shock_type,
            "magnitude": shock_magnitude,
            "simulation_result": simulation_result
        }

        if self.alert_dispatcher:
            self.alert_dispatcher.dispatch(result)

        return result

    def export_shock_report(self, report_id):
        try:
            import skills.market_portfolio_data_exporter as market_portfolio_data_exporter
            if hasattr(market_portfolio_data_exporter, "generate_stream"):
                return market_portfolio_data_exporter.generate_stream(report_id)
        except Exception:
            pass
        return io.BytesIO(f"Report stream for {report_id}".encode("utf-8"))

    def batch_simulate(self, portfolio_ids, shock_type, shock_magnitude):
        results = []
        for pid in portfolio_ids:
            if self.db_storage:
                portfolio = self.db_storage.get_portfolio(pid)
                if not portfolio:
                    raise ValueError(f"Portfolio {pid} not found")

            simulation_result = {}
            if self.scenario_sim:
                simulation_result = self.scenario_sim.run_scenario(pid, shock_type, shock_magnitude)

            event_id = uuid.uuid4()
            results.append({
                "event_id": event_id.hex,
                "portfolio_id": pid,
                "shock_type": shock_type,
                "magnitude": shock_magnitude,
                "simulation_result": simulation_result
            })
        return results


def market_portfolio_macro_shock_simulator(payload):
    try:
        from skills.db_storage import db_storage
    except Exception:
        db_storage = lambda payload: True

    shock_id = payload.get("shock_id", f"shock_{uuid.uuid4().hex[:8]}")
    portfolio_id = payload.get("portfolio_id")
    scenario_id = payload.get("scenario_id")
    assets = payload.get("assets", [])
    macro_variables = payload.get("macro_variables", {})

    inflation = macro_variables.get("inflation_shock", 0.05)
    rate_hike = macro_variables.get("central_bank_rate_hike", 25)

    shock_factor = 1.0 - (inflation + (rate_hike / 1000.0))

    impact_results = []
    for asset in assets:
        current_price = asset.get("current_price", 0.0)
        volume = asset.get("volume", 0)
        base_val = current_price * volume
        adjusted_valuation = base_val * shock_factor

        impact_results.append({
            "asset_id": asset.get("asset_id"),
            "ticker": asset.get("ticker"),
            "adjusted_valuation": adjusted_valuation
        })

    output = {
        "shock_id": shock_id,
        "portfolio_id": portfolio_id,
        "scenario_id": scenario_id,
        "impact_results": impact_results
    }

    try:
        db_storage({
            "action": "save_macro_simulation",
            "shock_id": shock_id,
            "data": output
        })
    except Exception:
        pass

    return output
