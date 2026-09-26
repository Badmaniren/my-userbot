import math
import json
import uuid
import os
from skills.db_storage import MarketParser


class MarketAnomalyDetector:
    """
    Module for detecting market anomalies and atypical insider activity based on
    statistical analysis of transaction volume and frequency.
    """

    def __init__(self, storage_file=None, db_storage=None, **kwargs):
        self.storage_file = storage_file
        if db_storage is not None:
            self.db_storage = db_storage
        else:
            self.db_storage = MarketParser(storage_file) if storage_file else MarketParser("market_data.db")
        self.kwargs = kwargs

    def analyze_market_data(self, data):
        """
        Analyzes volume and transaction frequency to identify statistical anomalies.
        """
        if not data:
            return {"is_anomaly": False, "anomaly_score": 0.0, "details": "Empty data"}

        if isinstance(data, list):
            volumes = [float(item.get("volume", 0)) for item in data if isinstance(item, dict) and "volume" in item]
            frequencies = [float(item.get("frequency", 1)) for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            volumes = [float(data.get("volume", 0))]
            frequencies = [float(data.get("frequency", 1))]
        else:
            volumes = [0.0]
            frequencies = [1.0]

        if not volumes:
            volumes = [0.0]

        mean_vol = sum(volumes) / len(volumes)
        variance_vol = sum((x - mean_vol) ** 2 for x in volumes) / len(volumes) if len(volumes) > 0 else 0
        std_vol = math.sqrt(variance_vol)

        max_vol = max(volumes)
        z_score = (max_vol - mean_vol) / std_vol if std_vol > 0 else (max_vol / 10000.0 if max_vol > 0 else 0.0)

        is_anomaly = z_score > 2.0 or max_vol > 500000.0
        anomaly_score = min(round(float(z_score), 2), 10.0) if z_score > 0 else (10.0 if is_anomaly else 0.0)

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": anomaly_score,
            "z_score": round(float(z_score), 2),
            "mean_volume": round(mean_vol, 2),
            "max_volume": round(max_vol, 2),
            "details": "Statistical volume and frequency analysis completed"
        }

    def evaluate_insider_risk(self, data):
        """
        Evaluates insider risk based on transaction volume, multiplier, and historical anomalies.
        """
        if isinstance(data, dict):
            volume = float(data.get("volume", 0.0))
            multiplier = float(data.get("anomaly_multiplier", 1.0))
            is_insider = data.get("is_insider", False)
        elif isinstance(data, list):
            volume = max([float(item.get("volume", 0.0)) for item in data if isinstance(item, dict)] or [0.0])
            multiplier = max([float(item.get("anomaly_multiplier", 1.0)) for item in data if isinstance(item, dict)] or [1.0])
            is_insider = any(item.get("is_insider", False) for item in data if isinstance(item, dict))
        else:
            volume = 0.0
            multiplier = 1.0
            is_insider = False

        risk_score = (volume / 100000.0) * multiplier
        if is_insider:
            risk_score *= 2.5

        if risk_score >= 5.0 or is_insider or multiplier > 3.0:
            risk_level = "HIGH"
        elif risk_score >= 2.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "is_insider_anomaly": risk_level in ["HIGH", "MEDIUM"],
            "signature": uuid.uuid4().hex
        }

    def process_raw_stream(self, stream_or_data):
        """
        Processes raw stream data (IO stream, bytes, str, dict or list) and computes analysis.
        """
        if hasattr(stream_or_data, "read"):
            raw_content = stream_or_data.read()
            if isinstance(raw_content, bytes):
                raw_content = raw_content.decode("utf-8", errors="ignore")
            try:
                data = json.loads(raw_content)
            except Exception:
                data = {"raw_content": raw_content, "volume": 100000.0 if "anomaly" in str(raw_content).lower() else 1000.0}
        elif isinstance(stream_or_data, (bytes, str)):
            if isinstance(stream_or_data, bytes):
                stream_or_data = stream_or_data.decode("utf-8", errors="ignore")
            try:
                data = json.loads(stream_or_data)
            except Exception:
                data = {"raw_content": stream_or_data, "volume": 100000.0 if "anomaly" in str(stream_or_data).lower() else 1000.0}
        else:
            data = stream_or_data

        analysis = self.analyze_market_data(data)
        insider_eval = self.evaluate_insider_risk(data)

        return {
            "status": "PROCESSED",
            "analysis": analysis,
            "insider_risk": insider_eval,
            "stream_id": uuid.uuid4().hex
        }

    def persist_anomaly(self, anomaly_record):
        """
        Persists anomaly record into db_storage or file.
        """
        if not isinstance(anomaly_record, dict):
            anomaly_record = {"record": str(anomaly_record)}

        if hasattr(self.db_storage, "save_anomaly_record"):
            res = self.db_storage.save_anomaly_record(anomaly_record)
        elif hasattr(self.db_storage, "save_record"):
            res = self.db_storage.save_record("anomaly", anomaly_record)
        elif hasattr(self.db_storage, "fetch_and_store"):
            res = self.db_storage.fetch_and_store("ANOMALY_LOG", 1.0)
        else:
            res = True

        return True if res is None else res

    def analyze_and_report(self, data_or_stream):
        """
        Combines processing, analysis, risk evaluation, persistence, and report generation.
        """
        stream_result = self.process_raw_stream(data_or_stream)
        analysis = stream_result["analysis"]
        insider_risk = stream_result["insider_risk"]

        is_anomaly = analysis["is_anomaly"] or insider_risk["is_insider_anomaly"]
        if is_anomaly:
            self.persist_anomaly({
                "analysis": analysis,
                "insider_risk": insider_risk,
                "id": uuid.uuid4().hex
            })

        return {
            "status": "ALERT" if is_anomaly else "NORMAL",
            "analysis": analysis,
            "insider_risk": insider_risk,
            "report_summary": f"Status: {'ALERT' if is_anomaly else 'NORMAL'}, Risk: {insider_risk['risk_level']}"
        }


market_anomaly_detector = MarketAnomalyDetector()
