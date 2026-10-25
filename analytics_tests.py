
import unittest
import pandas as pd

from analytics import (
    clean_fuel_data,
    calculate_mileage,
    calculate_full_tank_mileage,
    vehicle_expense_report,
    monthly_expense_report,
    vehicle_comparison_report,
    period_comparison_report,
    detect_unusual_consumption,
    prepare_chart_data
)


class TestAnalytics(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "vehicle_id": [1, 1, 1, 1, 2, 2],
            "vehicle_name": [
                "Car A", "Car A", "Car A", "Car A",
                "Bike B", "Bike B"
            ],
            "vehicle_type": [
                "Car", "Car", "Car", "Car", "Bike", "Bike"
            ],
            "fuel_type": [
                "Petrol", "Petrol", "Petrol", "Petrol",
                "Petrol", "Petrol"
            ],
            "entry_id": [1, 2, 3, 4, 5, 6],
            "fuel_date": pd.to_datetime([
                "2026-01-10", "2026-01-20",
                "2026-02-10", "2026-03-10",
                "2026-01-15", "2026-02-15"
            ]),
            "previous_odometer": [100, 200, 300, 400, 50, 130],
            "current_odometer": [200, 300, 400, 500, 130, 210],
            "fuel_litres": [5, 5, 5, 10, 4, 4],
            "price_per_litre": [100, 100, 100, 100, 100, 100],
            "distance": [100, 100, 100, 100, 80, 80],
            "mileage": [20, 20, 20, 10, 20, 20],
            "total_cost": [500, 500, 500, 1000, 400, 400]
        })

    def test_clean_fuel_data(self):
        result = clean_fuel_data(self.df.copy())
        self.assertEqual(len(result), 6)
        self.assertTrue((result["fuel_litres"] > 0).all())

    def test_clean_removes_invalid_records(self):
        data = self.df.copy()
        data.loc[0, "fuel_litres"] = -5

        result = clean_fuel_data(data)

        self.assertEqual(len(result), 5)

    def test_calculate_mileage(self):
        result = calculate_mileage(self.df.copy())

        self.assertEqual(result.loc[0, "distance_km"], 100)
        self.assertEqual(
            result.loc[0, "approx_mileage_km_per_litre"], 20
        )

    def test_full_tank_flag_missing(self):
        result = calculate_full_tank_mileage(self.df.copy())

        self.assertIn(
            "full_tank_mileage_km_per_litre", result.columns
        )
        self.assertTrue(
            result["full_tank_mileage_km_per_litre"].isna().all()
        )

    def test_vehicle_expense_report(self):
        data = calculate_mileage(self.df.copy())
        result = vehicle_expense_report(data)

        self.assertEqual(len(result), 2)
        self.assertIn("total_expense", result.columns)

    def test_monthly_expense_report(self):
        result = monthly_expense_report(self.df.copy())

        self.assertIn("month", result.columns)
        self.assertIn("total_fuel_litres", result.columns)
        self.assertTrue(result["month"].str.match(r"\d{4}-\d{2}").all())

    def test_vehicle_comparison_report(self):
        result = vehicle_comparison_report(self.df.copy())

        self.assertEqual(len(result), 2)
        self.assertIn("average_approx_mileage", result.columns)
        self.assertIn("overall_cost_per_km", result.columns)

    def test_period_comparison_report(self):
        result = period_comparison_report(
            self.df.copy(), "2026-01-01", "2026-01-31"
        )

        self.assertEqual(
            round(result["total_expense"].sum(), 2), 1400
        )

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            period_comparison_report(
                self.df.copy(), "2026-03-31", "2026-01-01"
            )

    def test_detect_unusual_consumption(self):
        data = self.df.copy()

        # Add a very low mileage reading for Car A.
        data.loc[3, "fuel_litres"] = 50

        data = calculate_mileage(data)
        result = detect_unusual_consumption(data, threshold=0.30)

        self.assertIn("unusual_consumption", result.columns)
        self.assertTrue(result["unusual_consumption"].any())

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            detect_unusual_consumption(self.df.copy(), threshold=1.5)

    def test_prepare_chart_data(self):
        data = calculate_mileage(self.df.copy())
        result = prepare_chart_data(data)

        self.assertIn("monthly_data", result)
        self.assertIn("vehicle_data", result)
        self.assertIsInstance(result["monthly_data"], pd.DataFrame)
        self.assertIsInstance(result["vehicle_data"], pd.DataFrame)


if __name__ == "__main__":
    unittest.main()
