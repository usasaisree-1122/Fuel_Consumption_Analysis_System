from calculations import calculate_mileage, calculate_fuel_cost, calculate_total_fuel

print("Testing Fuel Calculations")

# Test 1: Mileage
print("Mileage:", calculate_mileage(150, 5), "km/l")

# Test 2: Fuel Cost
print("Fuel Cost: Rs.", calculate_fuel_cost(5, 105))

# Test 3: Total Fuel
print("Total Fuel:", calculate_total_fuel(150, 30), "litres")

# Test 4: Zero fuel
try:
    print(calculate_mileage(150, 0))
except ValueError:
    print("Error handled: Fuel cannot be zero")

# Test 5: Negative distance
try:
    print(calculate_mileage(-150, 5))
except ValueError:
    print("Error handled: Distance cannot be negative")

print("Testing completed!")