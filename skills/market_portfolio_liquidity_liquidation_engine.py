import uuid
import os

from skills import market_portfolio_slippage_model
from skills import market_portfolio_execution_pipeline
from skills import market_portfolio_audit_log_exporter
from skills import market_insider_alert_pipeline
from skills import market_portfolio_monitor


class LiquidationEngine:
    def __init__(self, db_storage=None, slippage_model=None, notifier=None):
        self.db_storage = db_storage
        self.slippage_model = slippage_model
        self.notifier = notifier

    def execute_liquidation(self, portfolio_id, asset_ticker, volume, liquidation_price):
        if self.slippage_model and hasattr(self.slippage_model, 'calculate'):
            slippage = self.slippage_model.calculate(asset_ticker, volume, liquidation_price)
        else:
            slippage = market_portfolio_slippage_model.calculate(asset_ticker, volume, liquidation_price)

        if hasattr(slippage, '__float__'):
            slip_val = float(slippage)
        else:
            slip_val = float(slippage.calculate())

        final_price = float(liquidation_price) * (1.0 - slip_val)

        result = {
            'portfolio_id': portfolio_id,
            'asset': asset_ticker,
            'volume': volume,
            'initial_price': liquidation_price,
            'final_price': final_price,
            'slippage': slippage
        }
        return result

    def trigger_emergency_stop(self, event_id, critical_threshold):
        stream = market_portfolio_execution_pipeline.get_stream()
        data = stream.getvalue().decode('utf-8')

        if event_id not in data:
            data = f"{data}:{event_id}"

        success = True if len(data) > 0 else False

        status = {
            'success': success,
            'event_id': event_id,
            'threshold': critical_threshold,
            'stream_data': data
        }
        return status

    def log_liquidation_event(self, log_entry):
        market_portfolio_audit_log_exporter.export(log_entry)

    def process_insider_signal(self, alert_id, severity):
        market_insider_alert_pipeline.dispatch(alert_id=alert_id, level=severity)

    def process_liquidation(self, liquidation_payload):
        portfolio_id = liquidation_payload.get("portfolio_id")
        target_asset = liquidation_payload.get("target_asset")
        shock_multiplier = liquidation_payload.get("shock_multiplier", 0.01)

        valuation_snapshot = liquidation_payload.get("valuation_snapshot", {})
        if isinstance(valuation_snapshot, dict):
            initial_val = valuation_snapshot.get("valuation", 10000.0)
        else:
            initial_val = 10000.0

        final_valuation = initial_val * (1 - shock_multiplier)

        liquidation_result = {
            "liquidation_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "target_asset": target_asset,
            "final_valuation": final_valuation,
            "status": "LIQUIDATED"
        }
        return liquidation_result


def market_portfolio_liquidity_liquidation_engine():
    return LiquidationEngine()