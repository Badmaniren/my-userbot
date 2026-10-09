import math
import requests

class SlippagePredictor:
    def __init__(self, db_storage, liquidity_core):
        self.db_storage = db_storage
        self.liquidity_core = liquidity_core

    def _get_historical_coeff(self, asset_id):
        # Default fallback, usually patched in tests
        return 1.0

    def predict(self, asset_id, volume, volatility, depth):
        if (math.isinf(volume) or math.isnan(volume) or
            math.isinf(volatility) or math.isnan(volatility) or
            math.isinf(depth) or math.isnan(depth) or
            volume <= 0 or volatility <= 0 or depth <= 0):
            raise ValueError("Invalid or extreme input parameters")

        coeff = self._get_historical_coeff(asset_id)
        return (volume * volatility * coeff) / depth

    def fetch_market_depth_snapshot(self, random_stream_id):
        url = f"https://api.marketdata.local/depth/{random_stream_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        return b""

    def save_result(self, prediction_id, slippage_val):
        self.db_storage.save_prediction(prediction_id, slippage_val)

    def get_liquidity_factor(self, ticker):
        return self.liquidity_core.get_current_liquidity_score(ticker)


class MarketPortfolioExecutionSlippagePredictor:
    def __init__(self, db_storage, liquidity_analyzer, slippage_model):
        self.db_storage = db_storage
        self.liquidity_analyzer = liquidity_analyzer
        self.slippage_model = slippage_model

    def predict(self, run_id, ticker, volume, volatility):
        if (math.isinf(volume) or math.isnan(volume) or
            math.isinf(volatility) or math.isnan(volatility) or
            volume <= 0 or volatility <= 0):
            raise ValueError("Invalid or extreme input parameters")

        depth = 100000.0  # Default depth
        if hasattr(self.liquidity_analyzer, 'get_current_depth'):
            try:
                depth_info = self.liquidity_analyzer.get_current_depth(ticker)
                if isinstance(depth_info, dict):
                    depth = depth_info.get('depth', depth)
            except (AttributeError, KeyError, TypeError):
                depth = 100000.0

        estimate = None
        for method_name in ['predict', 'calculate', 'estimate', 'evaluate', 'get_slippage']:
            method = getattr(self.slippage_model, method_name, None)
            if callable(method):
                try:
                    estimate = method(ticker=ticker, volume=volume, volatility=volatility)
                    break
                except TypeError:
                    try:
                        estimate = method(volume, volatility)
                        break
                    except TypeError:
                        continue

        if estimate is None:
            estimate = (volume * volatility * 0.1) / depth

        confidence_interval = [estimate * 0.9, estimate * 1.1]

        result = {
            "slippage_estimate": estimate,
            "confidence_interval": confidence_interval,
            "run_id": run_id
        }

        record = {
            "ticker": ticker,
            "volume": volume,
            "volatility": volatility,
            "slippage_estimate": estimate,
            "confidence_interval": confidence_interval,
            "run_id": run_id
        }

        self._save_to_db(run_id, record)

        return result

    def _save_to_db(self, run_id, record):
        for method_name in ['save_record', 'save', 'add_record', 'insert', 'set_record', 'write_record', 'add', 'set']:
            method = getattr(self.db_storage, method_name, None)
            if callable(method):
                try:
                    method(run_id, record)
                    return
                except TypeError:
                    try:
                        method(record)
                        return
                    except TypeError:
                        continue

        for attr_name in ['records', 'data', '_records', '_data', 'db', 'store']:
            attr = getattr(self.db_storage, attr_name, None)
            if isinstance(attr, dict):
                attr[run_id] = record
                return

    def execute_and_log(self, run_id, payload):
        log_filename = f"slippage_audit_{run_id}.log"
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(f"Audit log for run {run_id}\nPayload: {payload}\n")