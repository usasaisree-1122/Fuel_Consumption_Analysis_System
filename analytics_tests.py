import unittest
import sys
import types

import pandas as pd
import numpy as np

# These tests check analytics calculations, not the MySQL connection.
# This placeholder lets analytics.py load even when MySQL is not installed.
database_module = types.ModuleType("db_connection")
database_module.get_connection = lambda: None
sys.modules["db_connection"] = database_module

from analytics import (
    clean_fuel_data,
    calculate_mileage,
    calculate_full_tank_mileage,
    vehicle_expense_report,
    monthly_expense_report,
    vehicle_comparison_report,
    period_comparison_report,
    detect_unusual_consumption,
    invalid_readings_report,
    prepare_chart_data
)


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        self.data = pd.DataFrame({
            "entry_id": [1, 2, 3, 4],
            "vehicle_id": [1, 1, 2, 2],
            "vehicle_name": ["Car A", "Car A", "Car B", "Car B"],
            "vehicle_number": [
                "AP01AA1111", "AP01AA1111",
                "AP02BB2222", "AP02BB2222"
            ],
            "fuel_date": pd.to_datetime([
                "2026-01-10", "2026-02-10",
                "2026-02-15", "2026-03-10"
            ]),
            "previous_odometer": [1000, 1100, 2000, 2100],
            "current_odometer": [1100, 1200, 2100, 2200],
            "distance": [100, 100, 100, 100],
            "fuel_litres": [5, 5, 10, 5],
            "price_per_litre": [100, 100, 100, 100],
            "mileage": [20, 20, 10, 20],
            "total_cost": [500, 500, 1000, 500]
        })

    def test_clean_data_keeps_valid_rows(self):
        cleaned = clean_fuel_data(self.data)
        self.assertEqual(len(cleaned), 4)

    def test_clean_data_removes_invalid_fuel(self):
        bad_data = self.data.copy()
        bad_data.loc[0, "fuel_litres"] = 0
        cleaned = clean_fuel_data(bad_data)
        self.assertEqual(len(cleaned), 3)

    def test_clean_data_removes_bad_odometer_order(self):
        bad_data = self.data.copy()
        bad_data.loc[0, "current_odometer"] = 900
        cleaned = clean_fuel_data(bad_data)
        self.assertEqual(len(cleaned), 3)

    def test_calculate_mileage(self):
        result = calculate_mileage(self.data)
        self.assertEqual(result.loc[0, "mileage"], 20)

    def test_full_tank_missing_flag(self):
        result = calculate_full_tank_mileage(self.data)
        self.assertTrue(np.isnan(result))

    def test_full_tank_with_flag(self):
        data = self.data.copy()
        data["full_tank_flag"] = [1, 1, 0, 1]
        result = calculate_full_tank_mileage(data)
        self.assertAlmostEqual(result, 300 / 15)

    def test_vehicle_expense_report(self):
        report = vehicle_expense_report(self.data)
        self.assertEqual(len(report), 2)
        car_a = report[report["vehicle_name"] == "Car A"].iloc[0]
        self.assertEqual(car_a["total_expense"], 1000)

    def test_monthly_expense_report(self):
        report = monthly_expense_report(self.data)
        self.assertEqual(len(report), 3)
        february = report[report["month"] == "2026-02"].iloc[0]
        self.assertEqual(february["total_expense"], 1500)

    def test_vehicle_comparison_report(self):
        report = vehicle_comparison_report(self.data)
        car_a = report[report["vehicle_name"] == "Car A"].iloc[0]
        self.assertAlmostEqual(car_a["average_mileage"], 20)

    def test_period_comparison_report(self):
        report = period_comparison_report(self.data)
        self.assertEqual(len(report), 2)
        self.assertIn("change", report.columns)

    def test_unusual_consumption(self):
        data = self.data.copy()
        data.loc[1, "mileage"] = 50
        result = detect_unusual_consumption(data, threshold=0.20)
        self.assertGreater(len(result), 0)

    def test_invalid_readings_report(self):
        data = self.data.copy()
        data.loc[0, "fuel_litres"] = 0
        result = invalid_readings_report(data)
        self.assertEqual(len(result), 1)
        self.assertIn("validation_reason", result.columns)

    def test_prepare_chart_data(self):
        result = prepare_chart_data(self.data)
        self.assertIn("monthly_expenses", result)
        self.assertIn("monthly_fuel", result)
        self.assertIn("vehicle_mileage", result)
        self.assertIn("vehicle_fuel", result)

    def test_empty_data(self):
        result = clean_fuel_data(pd.DataFrame())
        self.assertTrue(result.empty)

    def test_empty_monthly_report(self):
        result = monthly_expense_report(pd.DataFrame())
        self.assertTrue(result.empty)


if __name__ == "__main__":
    unittest.main()
