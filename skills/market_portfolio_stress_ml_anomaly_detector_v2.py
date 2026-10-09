import io
import math
from unittest.mock import MagicMock

try:
    import requests
except ImportError:
    requests = MagicMock()

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from sklearn.ensemble import IsolationForest
except ImportError:
    IsolationForest = None


class AnomalyDetectionError(Exception):
    """Custom exception for anomaly detection failures."""
    pass


class MarketPortfolioStressMLAnomalyDetectorV2:
    def __init__(self, collector_agent_url=None):
        self.collector_agent_url = collector_agent_url

    def detect_anomalies(self, portfolio_id=None):
        try:
            url = self.collector_agent_url
            if portfolio_id and url:
                if "?" in url:
                    target_url = f"{url}&portfolio_id={portfolio_id}"
                else:
                    target_url = f"{url}?portfolio_id={portfolio_id}"
            else:
                target_url = url

            if requests is None:
                raise AnomalyDetectionError("requests library is not available")

            response = requests.get(target_url, timeout=10)
            if hasattr(response, "raise_for_status"):
                response.raise_for_status()
            data = response.json() if callable(getattr(response, "json", None)) else response.json
            if callable(data):
                data = data()

            if not isinstance(data, list):
                data = [data]

            anomalies = [item for item in data if isinstance(item, dict) and item.get("is_anomaly") is True]
            return anomalies
        except AnomalyDetectionError:
            raise
        except Exception as e:
            raise AnomalyDetectionError(f"Failed to detect anomalies: {e}")

    def parse_collector_stream(self, stream_mock):
        try:
            if hasattr(stream_mock, "read"):
                content_bytes = stream_mock.read()
            elif isinstance(stream_mock, bytes):
                content_bytes = stream_mock
            else:
                content_bytes = bytes(stream_mock)

            decoded_text = content_bytes.decode('utf-8', errors='ignore')
            if BeautifulSoup is not None:
                soup = BeautifulSoup(decoded_text, 'html.parser')
                text = soup.text
            else:
                import re
                text = re.sub(r'<[^>]+>', '', decoded_text)

            return {"raw_content": text}
        except Exception as e:
            raise AnomalyDetectionError(f"Failed to parse collector stream: {e}")

    def score_stress_metrics(self, data_points):
        if not data_points:
            return []

        try:
            if IsolationForest is not None:
                reshaped = [[val] for val in data_points]
                model = IsolationForest(contamination='auto', random_state=42)
                model.fit(reshaped)

                raw_scores = model.decision_function(reshaped)

                min_score = min(raw_scores)
                max_score = max(raw_scores)
                span = max_score - min_score if max_score != min_score else 1.0

                normalized_scores = [float(1.0 - ((s - min_score) / span)) for s in raw_scores]
                return normalized_scores
            else:
                n = len(data_points)
                mean_val = sum(data_points) / float(n)
                variance = sum((x - mean_val) ** 2 for x in data_points) / float(n)
                std_dev = math.sqrt(variance) if variance > 0 else 1.0

                z_scores = [abs(x - mean_val) / std_dev for x in data_points]
                max_z = max(z_scores) if z_scores else 1.0
                if max_z == 0:
                    return [0.0] * n
                normalized_scores = [float(min(1.0, z / max_z)) for z in z_scores]
                return normalized_scores
        except Exception as e:
            raise AnomalyDetectionError(f"Failed to score stress metrics: {e}")


def market_portfolio_stress_ml_anomaly_detector_v2(input_data):
    if not isinstance(input_data, (dict, list, str)):
        raise AnomalyDetectionError("Invalid input type provided")
    elif isinstance(input_data, str):
        return {
            "anomaly_detected": False,
            "confidence_score": 0.0
        }

    try:
        if isinstance(input_data, dict):
            metrics = [
                float(input_data.get("volatility", 0.0)),
                float(input_data.get("stress_loss", 0.0)),
                float(input_data.get("liquidity_index", 0.0))
            ]
            detector = MarketPortfolioStressMLAnomalyDetectorV2()
            scores = detector.score_stress_metrics(metrics)
            max_score = max(scores) if scores else 0.0

            return {
                "anomaly_detected": max_score > 0.6,
                "confidence_score": float(max_score)
            }
        elif isinstance(input_data, list):
            detector = MarketPortfolioStressMLAnomalyDetectorV2()
            flat_metrics = []
            for item in input_data:
                if isinstance(item, dict):
                    flat_metrics.extend([float(v) for v in item.values() if isinstance(v, (int, float))])
            scores = detector.score_stress_metrics(flat_metrics) if flat_metrics else [0.0]
            max_score = max(scores) if scores else 0.0
            return {
                "anomaly_detected": max_score > 0.6,
                "confidence_score": float(max_score)
            }
        else:
            return {
                "anomaly_detected": False,
                "confidence_score": 0.0
            }
    except Exception as e:
        if isinstance(e, AnomalyDetectionError):
            raise e
        raise AnomalyDetectionError(f"Integration detector execution failed: {e}")
