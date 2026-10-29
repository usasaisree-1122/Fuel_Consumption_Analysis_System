
import math


def check_number(value, name):
    """Check that a value is a real, finite number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + " must be a number")

    if not math.isfinite(value):
        raise ValueError(name + " must be a finite number")


def calculate_mileage(distance, fuel_used):
    """Calculate kilometres travelled per litre."""
    check_number(distance, "Distance")
    check_number(fuel_used, "Fuel used")

    if distance < 0:
        raise ValueError("Distance cannot be negative")

    if fuel_used <= 0:
        raise ValueError("Fuel used must be greater than zero")

    return distance / fuel_used


def calculate_fuel_cost(fuel_used, price_per_litre):
    """Calculate total fuel expense."""
    check_number(fuel_used, "Fuel used")
    check_number(price_per_litre, "Price per litre")

    if fuel_used <= 0:
        raise ValueError("Fuel used must be greater than zero")

    if price_per_litre <= 0:
        raise ValueError("Price per litre must be greater than zero")

    return fuel_used * price_per_litre


def calculate_total_fuel(distance, mileage):
    """Calculate fuel required for a given distance."""
    check_number(distance, "Distance")
    check_number(mileage, "Mileage")

    if distance < 0:
        raise ValueError("Distance cannot be negative")

    if mileage <= 0:
        raise ValueError("Mileage must be greater than zero")

    return distance / mileage
