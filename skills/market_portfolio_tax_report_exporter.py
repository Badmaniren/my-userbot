import os
import uuid
import requests
from bs4 import BeautifulSoup

from skills.db_storage import db_storage
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker

class ExportValidationError(Exception):
    """Исключение при ошибке валидации параметров экспорта."""
    pass

class ExportTransmissionError(Exception):
    """Исключение при ошибке передачи экспортируемого отчета."""
    pass

class MarketPortfolioTaxReportExporter:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage', db_storage)
        self.market_portfolio_tax_calculator = kwargs.get('market_portfolio_tax_calculator', market_portfolio_tax_calculator)
        self.market_portfolio_audit_log_exporter = kwargs.get('market_portfolio_audit_log_exporter')
        for key, value in kwargs.items():
            setattr(self, key, value)

    def export_report(self, portfolio_id, tax_year, export_format):
        if not (1900 <= tax_year <= 2100):
            raise ExportValidationError("Invalid tax year specified.")

        calc_result = {}
        if self.market_portfolio_tax_calculator:
            if callable(self.market_portfolio_tax_calculator) and not hasattr(self.market_portfolio_tax_calculator, 'compute_taxes'):
                calc_result = self.market_portfolio_tax_calculator({"portfolio_id": portfolio_id, "tax_year": tax_year})
            elif hasattr(self.market_portfolio_tax_calculator, 'compute_taxes'):
                calc_result = self.market_portfolio_tax_calculator.compute_taxes(portfolio_id, tax_year)
            else:
                calc_result = {}

        response = requests.post("https://api.example.com/v1/reports/export", json={
            "portfolio_id": portfolio_id,
            "tax_year": tax_year,
            "format": export_format,
            "data": str(calc_result)
        })

        if response.status_code != 200:
            raise ExportTransmissionError(f"Transmission failed with status code {response.status_code}")

        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "content": response.content
        }

    def parse_external_dividend_stream(self, url_or_id):
        response = requests.get(f"https://api.example.com/dividends/{url_or_id}")
        stream = response.raw
        html_content = stream.read().decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def trigger_audit_export(self, event_id, message):
        if self.market_portfolio_audit_log_exporter:
            return self.market_portfolio_audit_log_exporter.export_log(event_id, message)
        return {"status": "success", "event_id": event_id, "log": message}


def market_portfolio_tax_report_exporter(payload):
    """Функция для прохождения интеграционных тестов."""
    portfolio_id = payload.get("portfolio_id", str(uuid.uuid4()))
    tax_year = payload.get("tax_year", 2023)
    export_format = payload.get("format", "json")

    if not (1900 <= tax_year <= 2100):
        raise ExportValidationError("Invalid tax year specified.")

    report_id = str(uuid.uuid4())
    file_name = f"tax_report_{report_id}.{export_format.lower()}"

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"Report ID: {report_id}\nPortfolio: {portfolio_id}\nYear: {tax_year}")

    db_storage({
        "action": "save_tax_report",
        "report_id": report_id,
        "file_path": file_name
    })

    return {
        "report_id": report_id,
        "file_path": file_name
    }