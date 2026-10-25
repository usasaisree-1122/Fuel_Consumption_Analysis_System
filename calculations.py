def calculate_mileage(distance, fuel_used):
    if distance < 0 or fuel_used < 0:
        raise ValueError("Distance and fuel cannot be negative")
    if fuel_used == 0:
        raise ValueError("Fuel used must be greater than zero")

    return distance / fuel_used


def calculate_fuel_cost(fuel_used, price_per_litre):
    if fuel_used < 0 or price_per_litre < 0:
        raise ValueError("Values cannot be negative")

    return fuel_used * price_per_litre


def calculate_total_fuel(distance, mileage):
    if distance < 0 or mileage <= 0:
        raise ValueError("Invalid distance or mileage")

    return distance / mileage

