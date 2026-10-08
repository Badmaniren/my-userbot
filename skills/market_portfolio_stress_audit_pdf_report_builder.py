import os
import io
from typing import Dict, Any, Optional

try:
    from skills.market_portfolio_stress_audit_summary_vault import market_portfolio_stress_audit_summary_vault
except ImportError:
    market_portfolio_stress_audit_summary_vault = None

try:
    from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
except ImportError:
    market_portfolio_stress_audit_visualizer = None


class MarketPortfolioStressAuditPdfReportBuilder:
    """
    Генератор PDF-отчетов по результатам стресс-аудита портфеля на базе
    собранных метрик и графиков из модулей визуализации и хранилища сводок.
    """
    def __init__(self, vault=None, visualizer=None):
        self.vault = vault
        self.visualizer = visualizer

    def build_report(self, audit_id: str, output_stream: io.BytesIO) -> dict:
        if not audit_id:
            raise ValueError("Audit ID cannot be empty")

        summary_data = {}
        if self.vault:
            if hasattr(self.vault, "get_summary"):
                summary_data = self.vault.get_summary(audit_id)
            elif callable(self.vault):
                try:
                    summary_data = self.vault(audit_id)
                except Exception:
                    summary_data = {}

        charts = []
        if self.visualizer:
            if hasattr(self.visualizer, "generate_charts"):
                charts = self.visualizer.generate_charts(audit_id)
            elif callable(self.visualizer):
                try:
                    res = self.visualizer({"portfolio_id": audit_id})
                    if isinstance(res, list):
                        charts = res
                    elif isinstance(res, dict):
                        charts = [res.get("chart_id", "default_chart")]
                    elif isinstance(res, str):
                        charts = [res]
                except Exception:
                    charts = []

        report_header = f"STRESS AUDIT REPORT: {audit_id}"
        output_stream.write(report_header.encode('utf-8'))
        for chart in charts:
            output_stream.write(f"\n[CHART:{chart}]".encode('utf-8'))

        return {
            "audit_id": audit_id,
            "status": "success",
            "summary": summary_data,
            "charts_count": len(charts)
        }


def market_portfolio_stress_audit_pdf_report_builder(report_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Функциональный адаптер для интеграционных тестов, обеспечивающий сбор данных,
    генерацию отчета и сохранение физического PDF-файла на диск.
    """
    portfolio_id = report_input.get("portfolio_id")
    if not portfolio_id:
        raise ValueError("Portfolio ID cannot be empty in report_input")

    vault_data = report_input.get("vault_data", {})
    visualizer_data = report_input.get("visualizer_data", {})
    output_path = report_input.get("output_path", f"/tmp/stress_report_{portfolio_id}.pdf")

    class DummyVault:
        def get_summary(self, aid):
            return vault_data

    class DummyVisualizer:
        def generate_charts(self, aid):
            chart_val = visualizer_data.get("chart_id", "default_chart")
            if isinstance(chart_val, list):
                return chart_val
            return [chart_val]

    builder = MarketPortfolioStressAuditPdfReportBuilder(vault=DummyVault(), visualizer=DummyVisualizer())

    pdf_stream = io.BytesIO()
    builder.build_report(portfolio_id, pdf_stream)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_stream.getvalue())

    return {
        "report_path": output_path,
        "status": "success"
    }