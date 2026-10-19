import os
import json

class AnomalyVisualizerError(Exception):
    """Исключение, выбрасываемое при ошибках в AnomalyVisualizer."""
    pass

class AnomalyVisualizer:
    def __init__(self, digest=None):
        if digest is not None and not isinstance(digest, dict):
            raise AnomalyVisualizerError("Digest must be a dictionary.")
        self.digest = digest if digest is not None else {}

    def render_text(self) -> str:
        lines = []
        lines.append(f"Digest ID: {self.digest.get('digest_id', '')}")
        lines.append(f"Title: {self.digest.get('title', '')}")
        lines.append(f"Severity: {self.digest.get('severity', '')}")
        
        metrics = self.digest.get("metrics", {})
        lines.append("Metrics:")
        for k, v in metrics.items():
            lines.append(f"  {k}: {v}")
            
        correlations = self.digest.get("correlations", [])
        lines.append("Correlations:")
        for c in correlations:
            lines.append(f"  {c.get('source')} -> {c.get('target')} : {c.get('coefficient')}")

        anomalies = self.digest.get("anomalies", [])
        if anomalies:
            lines.append("Anomalies:")
            for a in anomalies:
                if isinstance(a, dict):
                    lines.append(f"  Source: {a.get('source')} | Severity: {a.get('severity')} | Details: {a.get('details')}")

        return "\n".join(lines)

    def render_ascii_correlation_graph(self) -> str:
        correlations = self.digest.get("correlations", [])
        if not correlations:
            return "No correlations available."
        
        graph_lines = ["--- ASCII Correlation Graph ---"]
        for c in correlations:
            source = c.get("source", "unknown")
            target = c.get("target", "unknown")
            coef = c.get("coefficient", 0.0)
            graph_lines.append(f"[{source}] ===({coef:.2f})===> [{target}]")
            
        return "\n".join(graph_lines)

    def export_report(self, file_path: str) -> str:
        try:
            content = self.render_text() + "\n" + self.render_ascii_correlation_graph()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return file_path
        except IOError as e:
            raise AnomalyVisualizerError(f"Failed to export report: {e}")

    def get_summary_metrics(self) -> dict:
        return self.digest.get("metrics", {})

    def visualize_digest(self, data):
        """Поддерживает как один дайджест (dict), так и список аномалий от AnomalyLogger."""
        if isinstance(data, list):
            report_lines = ["--- Anomaly Logger Digest ---"]
            for item in data:
                source = item.get("source", "")
                severity = item.get("severity", "")
                details = item.get("details", "")
                report_lines.append(f"Source: {source} | Severity: {severity} | Details: {details}")
            return "\n".join(report_lines)
        elif isinstance(data, dict):
            self.digest = data
            return self.render_text()
        else:
            return str(data)