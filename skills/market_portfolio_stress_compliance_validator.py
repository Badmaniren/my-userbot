import os
import json
import sys
from skills.db_storage import get_audit_record, db_storage
from skills import market_portfolio_audit_compliance_hub


def start_new(*args, **kwargs):
    """
    Автоматическая проверка портфельных стресс-отчетов на соответствие регуляторным нормам.
    Поддерживает сигнатуру со всеми переданными моками и аргументами из юнит-тестов.
    """
    compliance_hub = kwargs.get('market_portfolio_audit_compliance_hub')

    # Если compliance_hub не передан в kwargs, используем модуль/атрибут модуля
    current_module = sys.modules.get(__name__)
    if compliance_hub is None and current_module and hasattr(current_module, 'market_portfolio_audit_compliance_hub'):
        compliance_hub = getattr(current_module, 'market_portfolio_audit_compliance_hub')
    if compliance_hub is None:
        compliance_hub = globals().get('market_portfolio_audit_compliance_hub')

    report_id = kwargs.get('report_id')
    threshold = kwargs.get('threshold', 0.5)

    if compliance_hub is not None:
        return compliance_hub.validate_report(report_id, threshold)

    raise RuntimeError("Compliance hub is not initialized")


def validate_portfolio_stress_compliance(audit_id: str) -> dict:
    """
    Интеграционная проверка стресс-отчета на основе данных из хранилища аудита.
    Считывает реальные данные, выполняет валидацию и создает реальный артефакт на диске.
    """
    record = get_audit_record(audit_id)
    if not record:
        raise ValueError(f"Audit record {audit_id} not found in database storage.")

    portfolio_id = record.get("portfolio_id")
    report_id = record.get("report_id")
    shock_factor = record.get("shock_factor", 0.0)

    # Регуляторная проверка: шок-фактор не должен превышать критический порог 0.30
    is_compliant = shock_factor <= 0.30

    validation_result = {
        "audit_id": audit_id,
        "portfolio_id": portfolio_id,
        "report_id": report_id,
        "shock_factor": shock_factor,
        "is_compliant": is_compliant,
        "status": "COMPLIANT" if is_compliant else "NON_COMPLIANT"
    }

    output_artifact_path = f"compliance_report_{audit_id}.log"
    with open(output_artifact_path, "w", encoding="utf-8") as f:
        json.dump(validation_result, f, ensure_ascii=False, indent=4)

    return validation_result
