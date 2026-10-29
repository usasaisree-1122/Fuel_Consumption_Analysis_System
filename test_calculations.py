
import unittest

from calculations import (
    calculate_mileage,
    calculate_fuel_cost,
    calculate_total_fuel
)


class TestCalculations(unittest.TestCase):

    def test_mileage(self):
        self.assertEqual(calculate_mileage(100, 5), 20)

    def test_mileage_with_decimal(self):
        self.assertAlmostEqual(calculate_mileage(150, 10), 15)

    def test_zero_fuel_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage(100, 0)

    def test_negative_fuel_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage(100, -5)

    def test_negative_distance_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage(-100, 5)

    def test_text_input_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage("100", 5)

    def test_boolean_input_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage(True, 5)

    def test_infinite_input_rejected(self):
        with self.assertRaises(ValueError):
            calculate_mileage(float("inf"), 5)

    def test_fuel_cost(self):
        self.assertEqual(calculate_fuel_cost(10, 100), 1000)

    def test_zero_fuel_cost_rejected(self):
        with self.assertRaises(ValueError):
            calculate_fuel_cost(0, 100)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):
            calculate_fuel_cost(10, -100)

    def test_total_fuel_required(self):
        self.assertEqual(calculate_total_fuel(100, 20), 5)

    def test_zero_mileage_rejected(self):
        with self.assertRaises(ValueError):
            calculate_total_fuel(100, 0)

    def test_negative_distance_for_fuel(self):
        with self.assertRaises(ValueError):
            calculate_total_fuel(-100, 20)


if __name__ == "__main__":
    unittest.main()
