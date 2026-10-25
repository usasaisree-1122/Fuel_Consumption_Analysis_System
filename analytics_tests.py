import unittest
import pandas as pd

from analytics import (
    clean_fuel_data,
    calculate_mileage,
    calculate_full_tank_mileage,
    vehicle_expense_report,
    monthly_expense_report,
    detect_unusual_consumption
)


class AnalyticsTests(unittest.TestCase):

    def setUp(self):
        # Sample data used for testing
        self.df = pd.DataFrame({
            "vehicle_id": [1, 1, 1, 1, 2, 2],
            "vehicle_code": [
                "VH001", "VH001", "VH001", "VH001",
                "VH002", "VH002"
            ],
            "vehicle_type": [
                "Car", "Car", "Car", "Car", "Bike", "Bike"
            ],
            "fuel_type": [
                "Petrol", "Petrol", "Petrol", "Petrol",
                "Petrol", "Petrol"
            ],
            "record_id": [1, 2, 3, 4, 5, 6],
            "fill_date": pd.to_datetime([
                "2026-01-01",
                "2026-01-10",
                "2026-01-20",
                "2026-01-30",
                "2026-01-05",
                "2026-01-15"
            ]),
            "odometer_km": [
                1000, 1100, 1200, 1230, 500, 700
            ],
            "litres": [10, 10, 10, 10, 5, 5],
            "total_cost": [1000, 1000, 1000, 1000, 500, 500],
            "full_tank_flag": [
                True, True, True, True, True, True
            ]
        })

    def test_clean_fuel_data(self):
        result = clean_fuel_data(self.df)

        self.assertEqual(len(result), 6)
        self.assertTrue((result["litres"] > 0).all())

    def test_calculate_mileage(self):
        result = calculate_mileage(self.df)

        # VH001: (1100 - 1000) / 10 = 10 km/litre
        self.assertAlmostEqual(
            result.loc[1, "approx_mileage_km_per_litre"],
            10.0
        )

    def test_full_tank_mileage(self):
        result = calculate_mileage(self.df)
        result = calculate_full_tank_mileage(result)

        # VH001: (1230 - 1200) / 10 = 3 km/litre
        self.assertAlmostEqual(
            result.loc[3, "full_tank_mileage_km_per_litre"],
            3.0
        )

    def test_vehicle_expense_report(self):
        result = vehicle_expense_report(self.df)

        # VH001 has four records, each costing 1000
        vh001 = result[
            result["vehicle_code"] == "VH001"
        ]

        self.assertEqual(
            vh001.iloc[0]["total_expense"],
            4000
        )

    def test_monthly_expense_report(self):
        result = monthly_expense_report(self.df)

        self.assertIn("month", result.columns)
        self.assertIn("total_expense", result.columns)

    def test_detect_unusual_consumption(self):
        result = calculate_mileage(self.df)
        result = detect_unusual_consumption(result)

        # VH001 mileage values are 10, 10 and 3.
        # The 3 km/litre reading is unusually low.
        self.assertTrue(
            result.loc[3, "unusual_consumption"]
        )


if __name__ == "__main__":
    unittest.main()