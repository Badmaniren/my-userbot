import unittest
import uuid
import random
from unittest.mock import patch
from skills.incident_business_loss_calculator import calculate_business_loss, incident_business_loss_calculator

class TestIncidentBusinessLossCalculator(unittest.TestCase):
    def test_calculate_business_loss_basic(self):
        inc_id = uuid.uuid4().hex
        downtime = random.randint(10, 300)
        hourly_rev = round(random.uniform(100.0, 5000.0), 2)
        curr = random.choice(["USD", "EUR", "GBP"])

        result = calculate_business_loss(
            incident_id=inc_id,
            downtime_minutes=downtime,
            hourly_revenue=hourly_rev,
            currency=curr
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), inc_id)
        self.assertEqual(result.get("currency"), curr)
        expected_loss = round((downtime / 60.0) * hourly_rev, 2)
        self.assertEqual(result.get("total_financial_loss"), expected_loss)

    def test_incident_business_loss_calculator_wrapper(self):
        inc_id = uuid.uuid4().hex
        payload = {
            "incident_id": inc_id,
            "downtime_minutes": random.randint(5, 120),
            "hourly_revenue": round(random.uniform(50.0, 1000.0), 2),
            "currency": "EUR"
        }

        result = incident_business_loss_calculator(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), inc_id)
        self.assertIn("total_financial_loss", result)

    def test_calculate_business_loss_with_impact_data(self):
        inc_id = uuid.uuid4().hex
        downtime = random.randint(15, 90)
        users = random.randint(100, 5000)
        payload = {
            "incident_id": inc_id,
            "impact_data": {
                "downtime_minutes": downtime,
                "affected_users": users
            },
            "hourly_revenue": 1200.0,
            "currency": "USD"
        }

        result = calculate_business_loss(payload)
        self.assertEqual(result.get("incident_id"), inc_id)
        expected_score = float(users) * (downtime / 60.0)
        self.assertEqual(result.get("operational_impact_score"), expected_score)
        self.assertEqual(result.get("operational_loss_index"), expected_score)

    def test_calculate_business_loss_with_revenue_per_minute(self):
        inc_id = uuid.uuid4().hex
        rpm = round(random.uniform(10.0, 100.0), 2)
        downtime = random.randint(10, 60)

        result = calculate_business_loss(
            incident_id=inc_id,
            downtime_minutes=downtime,
            revenue_per_minute=rpm
        )

        self.assertEqual(result.get("incident_id"), inc_id)
        expected_loss = round(downtime * rpm, 2)
        self.assertEqual(result.get("total_financial_loss"), expected_loss)