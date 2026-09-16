from skills.incident_impact_analyzer import incident_impact_analyzer
from skills.incident_severity_evaluator import incident_severity_evaluator

def calculate_business_loss(incident_id=None, downtime_minutes=0, hourly_revenue=0.0, affected_users=0, currency="USD", impact_data=None, revenue_per_minute=None, **kwargs):
    if isinstance(incident_id, dict):
        payload = incident_id
        incident_id = payload.get("incident_id")
        impact_data = payload.get("impact_data")
        revenue_per_minute = payload.get("revenue_per_minute")
        currency = payload.get("currency", currency)

    if impact_data and isinstance(impact_data, dict):
        downtime_minutes = impact_data.get("downtime_minutes", downtime_minutes)
        affected_users = impact_data.get("affected_users", affected_users)

    if revenue_per_minute is not None:
        hourly_revenue = revenue_per_minute * 60.0

    dt = float(downtime_minutes or 0)
    hr = float(hourly_revenue or 0.0)

    total_financial_loss = round((dt / 60.0) * hr, 2)

    if revenue_per_minute is not None:
        expected_min = dt * revenue_per_minute
        if total_financial_loss < expected_min:
            total_financial_loss = round(expected_min, 2)

    operational_impact_score = float(affected_users) * (dt / 60.0) if affected_users else dt

    return {
        "incident_id": incident_id,
        "total_financial_loss": total_financial_loss,
        "currency": currency,
        "operational_impact_score": operational_impact_score,
        "operational_loss_index": operational_impact_score
    }

def incident_business_loss_calculator(payload):
    if isinstance(payload, dict):
        return calculate_business_loss(payload)
    return calculate_business_loss(incident_id=payload)