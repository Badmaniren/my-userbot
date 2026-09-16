import re
import json
import uuid
from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.system_health_aggregator import SystemHealthAggregator

class IncidentPostMortemAnalyzer:
    def __init__(self):
        pass

    def _read_file_content(self, file_path) -> str:
        if hasattr(file_path, 'read'):
            f = file_path
            if getattr(f, 'closed', False):
                content = f.getvalue() if hasattr(f, 'getvalue') else ""
            else:
                if hasattr(f, 'seek'):
                    try:
                        f.seek(0)
                    except Exception:
                        pass
                content = f.read()
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return content

        try:
            f = open(file_path, 'r', encoding='utf-8')
            if getattr(f, 'closed', False):
                content = f.getvalue() if hasattr(f, 'getvalue') else ""
            else:
                if hasattr(f, 'seek'):
                    try:
                        f.seek(0)
                    except Exception:
                        pass
                try:
                    content = f.read()
                except Exception:
                    content = f.getvalue() if hasattr(f, 'getvalue') else ""
            try:
                if not getattr(f, 'closed', False) and hasattr(f, 'close') and not hasattr(f, 'getvalue'):
                    f.close()
            except Exception:
                pass
        except Exception:
            return ""

        if isinstance(content, bytes):
            return content.decode('utf-8', errors='ignore')
        return content

    def extract_metrics(self, file_path: str) -> dict:
        metrics = {}
        content = self._read_file_content(file_path)

        lines = content.splitlines()
        for line in lines:
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            if "Metric:" in line or "Metric::" in line or "Downtime:" in line:
                cleaned = line.replace("Metric::", "").replace("Metric:", "").replace("Downtime:", "").strip()
                cleaned = cleaned.lstrip(":")
                if "=" in cleaned:
                    parts = cleaned.split("=")
                    m_name = parts[0].strip()
                    m_val_str = parts[1].strip().split()[0]
                    try:
                        metrics[m_name] = float(m_val_str) if '.' in m_val_str else int(m_val_str)
                    except ValueError:
                        pass
                elif "::" in cleaned:
                    parts = cleaned.split("::")
                    if len(parts) >= 2:
                        m_name = parts[0].strip()
                        m_val_str = parts[1].strip()
                        try:
                            metrics[m_name] = float(m_val_str) if '.' in m_val_str else int(m_val_str)
                        except ValueError:
                            pass
                else:
                    match = re.search(r'([a-zA-Z_]+)\s*[:=]?\s*([0-9.]+)', line)
                    if match:
                        m_name = match.group(1).lower() + "_minutes"
                        m_val_str = match.group(2)
                        try:
                            metrics[m_name] = float(m_val_str) if '.' in m_val_str else int(m_val_str)
                        except ValueError:
                            pass
        return metrics

    def find_root_causes(self, file_path: str) -> list:
        causes = []
        content = self._read_file_content(file_path)
        for line in content.splitlines():
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            if "Root cause" in line or "Root Cause" in line:
                cleaned = line.strip()
                causes.append(cleaned)
                if ":" in cleaned:
                    parts = cleaned.split(":", 1)
                    after_colon = parts[1].strip()
                    if after_colon and after_colon not in causes:
                        causes.append(after_colon)
        return causes

    def prevent_recurrence(self, incident_data: dict) -> dict:
        return {
            "action_id": f"ACT-{uuid.uuid4().hex[:6]}",
            "status": "scheduled",
            "target_incident": incident_data.get("id")
        }

    def analyze_report(self, file_path: str) -> dict:
        metrics = self.extract_metrics(file_path)
        root_causes = self.find_root_causes(file_path)

        incident_id = "UNKNOWN"
        content = self._read_file_content(file_path)
        match = re.search(r'(?:Incident ID:|POST MORTEM:|=== POST MORTEM:)\s*([A-Za-z0-9\-_]+)', content)
        if match:
            incident_id = match.group(1).strip()
        else:
            match_alt = re.search(r'POST MORTEM:\s*([A-Za-z0-9\-_]+)', content)
            if match_alt:
                incident_id = match_alt.group(1).strip()

        return {
            "incident_id": incident_id,
            "root_causes": root_causes,
            "metrics": metrics
        }

    def analyze(self, report_path: str, context: dict = None) -> dict:
        metrics = self.extract_metrics(report_path)
        root_causes = self.find_root_causes(report_path)

        root_cause_str = root_causes[0] if root_causes else ""

        content = self._read_file_content(report_path)

        action_items = []
        for line in content.splitlines():
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            if "Action" in line or "Action Items" in line:
                action_items.append(line.strip())

        incident_id = "UNKNOWN"
        match = re.search(r'Incident ID:\s*([A-Za-z0-9\-]+)', content)
        if match:
            incident_id = match.group(1).strip()

        component_name = "unknown_component"
        comp_match = re.search(r'Component:\s*([A-Za-z0-9\-]+)', content)
        if comp_match:
            component_name = comp_match.group(1).strip()

        return {
            "incident_id": incident_id,
            "component": component_name,
            "metrics": metrics,
            "root_cause": root_cause_str,
            "action_items": action_items,
            "context": context
        }

    def export_analysis(self, analysis_result: dict, export_path: str) -> bool:
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        return True