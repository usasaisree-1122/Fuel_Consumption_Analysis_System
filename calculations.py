
# Calculate mileage in kilometres per litre
def calculate_mileage(distance, fuel_used):
    if not isinstance(distance, (int, float)) or isinstance(distance, bool):
        raise ValueError("Distance must be a number")

    if not isinstance(fuel_used, (int, float)) or isinstance(fuel_used, bool):
        raise ValueError("Fuel used must be a number")

    if distance < 0:
        raise ValueError("Distance cannot be negative")

    if fuel_used <= 0:
        raise ValueError("Fuel used must be greater than zero")

    return distance / fuel_used


# Calculate total fuel cost
def calculate_fuel_cost(fuel_used, price_per_litre):
    if not isinstance(fuel_used, (int, float)) or isinstance(fuel_used, bool):
        raise ValueError("Fuel used must be a number")

    if not isinstance(price_per_litre, (int, float)) or isinstance(price_per_litre, bool):
        raise ValueError("Price must be a number")

    if fuel_used < 0:
        raise ValueError("Fuel used cannot be negative")

    if price_per_litre < 0:
        raise ValueError("Price cannot be negative")

    return fuel_used * price_per_litre


# Calculate fuel required for a journey
def calculate_total_fuel(distance, mileage):
    if not isinstance(distance, (int, float)) or isinstance(distance, bool):
        raise ValueError("Distance must be a number")

    if not isinstance(mileage, (int, float)) or isinstance(mileage, bool):
        raise ValueError("Mileage must be a number")

    if distance < 0:
        raise ValueError("Distance cannot be negative")

    if mileage <= 0:
        raise ValueError("Mileage must be greater than zero")

    return distance / mileage
