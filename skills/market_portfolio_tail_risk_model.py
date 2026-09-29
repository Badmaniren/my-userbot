import sys

try:
    import skills.market_anomaly_detector as market_anomaly_detector
except ImportError:
    market_anomaly_detector = None


def _percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return float(sorted_data[0])
    p = max(0.0, min(100.0, float(p)))
    k = (n - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= n:
        return float(sorted_data[-1])
    d0 = sorted_data[f] * (c - k) + sorted_data[c] * (k - f)
    return float(d0)


class TailRiskConfig:
    def __init__(self, confidence=0.95, simulation_runs=1000):
        self.confidence = confidence
        self.simulation_runs = simulation_runs


class TailRiskModel:
    def __init__(self, portfolio_id=None, confidence_level=0.95):
        self.portfolio_id = portfolio_id
        self.confidence_level = confidence_level

    def calculate_var_and_es(self, returns):
        if not returns:
            raise ValueError("Returns list cannot be empty.")

        alpha = 1.0 - self.confidence_level
        var = _percentile(returns, alpha * 100)

        tail_losses = [r for r in returns if r <= var]
        if tail_losses:
            es = float(sum(tail_losses) / len(tail_losses))
        else:
            es = var

        return var, es

    def evaluate_historical_tail_risk(self, db_storage, storage_key):
        history = db_storage.fetch_historical_returns(storage_key)
        var, es = self.calculate_var_and_es(history)
        return {
            'var': var,
            'expected_shortfall': es,
            'portfolio_id': self.portfolio_id
        }

    def export_report(self, metrics):
        text = str(metrics) + '\n'
        try:
            sys.stdout.write(text)
        except TypeError:
            sys.stdout.write(text.encode('utf-8'))
        if hasattr(sys.stdout, 'flush'):
            sys.stdout.flush()

    def process_anomaly_trigger(self, anomaly_id):
        if market_anomaly_detector and hasattr(market_anomaly_detector, 'analyze_tail_event'):
            anomaly_payload = market_anomaly_detector.analyze_tail_event(anomaly_id)
        else:
            anomaly_payload = {'anomaly_id': anomaly_id, 'severity': 'LOW', 'drop_rate': 0.1}

        anomaly_payload['status'] = 'PROCESSED'
        return anomaly_payload


def calculate_tail_risk(retrieved_data, config: TailRiskConfig):
    assets = retrieved_data.get("assets", [])
    if not assets:
        return {"var": 0.0, "expected_shortfall": 0.0}

    weights = []
    returns_matrix = []

    for asset in assets:
        weights.append(asset.get("weight", 0.0))
        returns_matrix.append(asset.get("historical_returns", []))

    sum_weights = sum(weights)
    if sum_weights > 0:
        weights = [w / sum_weights for w in weights]
    else:
        weights = [1.0 / len(weights)] * len(weights)

    num_assets = len(assets)
    min_len = min((len(r) for r in returns_matrix if r), default=0)

    if min_len == 0:
        portfolio_returns = [0.0]
    else:
        portfolio_returns = []
        for t in range(min_len):
            r_t = sum(weights[i] * returns_matrix[i][t] for i in range(num_assets))
            portfolio_returns.append(r_t)

    alpha = 1.0 - config.confidence
    var = _percentile(portfolio_returns, alpha * 100)

    tail_losses = [r for r in portfolio_returns if r <= var]
    if tail_losses:
        es = float(sum(tail_losses) / len(tail_losses))
    else:
        es = var

    return {
        "var": var,
        "expected_shortfall": es
    }