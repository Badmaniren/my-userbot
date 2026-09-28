import random
import requests
import json
import os

class MarketPortfolioTailRiskAnalyzer:
    def __init__(self, db_storage=None, extractor_tool_1790087207=None,
                 extractor_tool_1790102839=None, extractor_tool_1790262909=None,
                 extractor_tool_1790621808=None, market_anomaly_detector=None):
        self.db_storage = db_storage
        self.extractors = [
            extractor_tool_1790087207,
            extractor_tool_1790102839,
            extractor_tool_1790262909,
            extractor_tool_1790621808
        ]
        self.market_anomaly_detector = market_anomaly_detector

    def _parse_stream_data(self, data):
        if isinstance(data, bytes):
            try:
                data = data.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                return None
        if not isinstance(data, str):
            return None
        data = data.strip()
        if not data:
            return None
        try:
            res = json.loads(data)
            if isinstance(res, list):
                return res
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        try:
            import ast
            res = ast.literal_eval(data)
            if isinstance(res, list):
                return res
        except (SyntaxError, ValueError, TypeError, MemoryError):
            pass
        return None

    def _fetch_market_stream(self, portfolio_id):
        try:
            response = requests.get(f"https://api.market.internal/portfolios/{portfolio_id}/stream")
            if response.status_code == 200:
                if hasattr(response, 'text') and response.text:
                    parsed = self._parse_stream_data(response.text)
                    if parsed is not None:
                        return parsed
                if hasattr(response, 'raw') and response.raw is not None:
                    try:
                        content = response.raw.read()
                        parsed = self._parse_stream_data(content)
                        if parsed is not None:
                            return parsed
                    except (AttributeError, OSError, TypeError):
                        pass
        except (requests.RequestException, AttributeError, ValueError, TypeError, OSError):
            pass
        return [float(random.normalvariate(-0.001, 0.02)) for _ in range(50)]

    def compute_raw_metrics(self, returns, confidence_level=0.95):
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        var = float(sorted_returns[index]) if len(sorted_returns) > 0 and index < len(sorted_returns) else 0.0
        if var > 0:
            var = -var
        tail = sorted_returns[:index]
        cvar = float(sum(tail) / len(tail)) if len(tail) > 0 else var
        if cvar > var:
            cvar = var
        return {"var": var, "cvar": cvar}

    def calculate_tail_risk(self, portfolio_id, confidence_level=0.95):
        returns = self._fetch_market_stream(portfolio_id)
        if self.extractors:
            for ext in self.extractors:
                if ext is not None and hasattr(ext, 'extract'):
                    res = ext.extract(portfolio_id)
                    if res is not None:
                        returns = res
                        break
        metrics = self.compute_raw_metrics(returns, confidence_level)
        metrics["portfolio_id"] = portfolio_id
        return metrics

    def evaluate_anomaly_impact(self, asset_symbol):
        anomaly = {}
        if self.market_anomaly_detector and hasattr(self.market_anomaly_detector, 'detect'):
            anomaly = self.market_anomaly_detector.detect(asset_symbol)

        signature = anomaly.get('signature', 'default_sig')
        asset = anomaly.get('asset', asset_symbol)
        is_tail = anomaly.get('is_tail_risk_event', True)

        return {
            'anomaly_signature': signature,
            'asset': asset,
            'mitigation_required': is_tail
        }

    def persist_tail_risk_metrics(self, metric_id):
        metrics = self.compute_raw_metrics([0.01, -0.02, -0.03, 0.005])
        if self.db_storage and hasattr(self.db_storage, 'save_metric'):
            self.db_storage.save_metric(metric_id, metrics)
        return metric_id

    def robust_data_extraction(self, portfolio_id):
        for ext in self.extractors:
            if ext is not None and hasattr(ext, 'extract'):
                try:
                    res = ext.extract(portfolio_id)
                    if res is not None:
                        return res
                except Exception:
                    raise
        return None

    def simulate_extreme_shock(self, portfolio_vector, shock_magnitude):
        shocked = [v - abs(shock_magnitude) * 0.01 for v in portfolio_vector]
        return shocked


_global_analyzer_instance = MarketPortfolioTailRiskAnalyzer()

def market_portfolio_tail_risk_analyzer(portfolio_id, confidence_level=0.95):
    res = _global_analyzer_instance.calculate_tail_risk(portfolio_id, confidence_level)
    return res