
import unittest

from calculations import (
    calculate_mileage,
    calculate_fuel_cost,
    calculate_total_fuel
)


class TestCalculations(unittest.TestCase):

    # Test 1: Normal mileage calculation
    def test_calculate_mileage(self):
        self.assertEqual(calculate_mileage(150, 5), 30)

    # Test 2: Zero fuel should raise an error
    def test_zero_fuel(self):
        with self.assertRaises(ValueError):
            calculate_mileage(150, 0)

    # Test 3: Negative distance should raise an error
    def test_negative_distance(self):
        with self.assertRaises(ValueError):
            calculate_mileage(-150, 5)

    # Test 4: Normal fuel cost calculation
    def test_calculate_fuel_cost(self):
        self.assertEqual(calculate_fuel_cost(5, 105), 525)

    # Test 5: Negative fuel cost input
    def test_negative_fuel_cost_input(self):
        with self.assertRaises(ValueError):
            calculate_fuel_cost(-5, 105)

    # Test 6: Normal total fuel calculation
    def test_calculate_total_fuel(self):
        self.assertEqual(calculate_total_fuel(150, 30), 5)

    # Test 7: Zero mileage should raise an error
    def test_zero_mileage(self):
        with self.assertRaises(ValueError):
            calculate_total_fuel(150, 0)

    # Test 8: Text input should raise an error
    def test_text_input(self):
        with self.assertRaises(ValueError):
            calculate_mileage("hello", 5)

    # Test 9: Negative fuel price should raise an error
    def test_negative_price(self):
        with self.assertRaises(ValueError):
            calculate_fuel_cost(5, -105)

    # Test 10: Boolean input should raise an error
    def test_boolean_input(self):
        with self.assertRaises(ValueError):
            calculate_mileage(True, 5)


if __name__ == "__main__":
    unittest.main()
