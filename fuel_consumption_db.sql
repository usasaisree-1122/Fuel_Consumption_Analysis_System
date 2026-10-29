
-- 1. Create the database
CREATE DATABASE IF NOT EXISTS fuel_consumption_db;

USE fuel_consumption_db;


-- 2. Create the vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_name VARCHAR(100) NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50),
    fuel_type VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 3. Create the fuel entries table
CREATE TABLE IF NOT EXISTS fuel_entries (
    entry_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    fuel_date DATE NOT NULL,
    previous_odometer DECIMAL(10,2) NOT NULL,
    current_odometer DECIMAL(10,2) NOT NULL,
    fuel_litres DECIMAL(10,2) NOT NULL,
    price_per_litre DECIMAL(10,2) NOT NULL,
    distance DECIMAL(10,2),
    mileage DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id)
);

-- Invalid_readings table

CREATE TABLE invalid_readings (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NULL,
    entered_date DATE NULL,
    previous_odometer DECIMAL(10,2) NULL,
    current_odometer DECIMAL(10,2) NULL,
    fuel_litres DECIMAL(10,2) NULL,
    reason VARCHAR(255) NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Insert sample vehicles
INSERT INTO vehicles
(vehicle_name, vehicle_number, vehicle_type, fuel_type)
VALUES
('Honda Activa', 'AP03AB1001', 'Scooter', 'Petrol'),
('Hyundai i20', 'AP03CD2002', 'Car', 'Petrol'),
('Royal Enfield Classic', 'AP03EF3003', 'Bike', 'Petrol'),
('Tata Nexon', 'AP03GH4004', 'Car', 'Diesel'),
('Maruti Swift', 'AP03IJ5005', 'Car', 'Petrol');


-- 5. Insert sample fuel entries
INSERT INTO fuel_entries
(vehicle_id, fuel_date, previous_odometer, current_odometer,
 fuel_litres, price_per_litre, distance, mileage, total_cost)
VALUES
(1, '2026-01-05', 1000, 1150, 3, 110, 150, 50, 330),
(1, '2026-02-05', 1150, 1300, 3.2, 110, 150, 46.88, 352),
(1, '2026-03-05', 1300, 1450, 3.1, 110, 150, 48.39, 341),
(1, '2026-04-05', 1450, 1600, 3, 112, 150, 50, 336),
(1, '2026-05-05', 1600, 1750, 3.3, 112, 150, 45.45, 369.6),

(2, '2026-01-10', 5000, 5300, 20, 105, 300, 15, 2100),
(2, '2026-02-10', 5300, 5600, 21, 105, 300, 14.29, 2205),
(2, '2026-03-10', 5600, 5900, 19, 106, 300, 15.79, 2014),
(2, '2026-04-10', 5900, 6200, 20, 106, 300, 15, 2120),
(2, '2026-05-10', 6200, 6500, 22, 106, 300, 13.64, 2332),

(3, '2026-01-12', 2000, 2200, 5, 110, 200, 40, 550),
(3, '2026-02-12', 2200, 2400, 5.2, 110, 200, 38.46, 572),
(3, '2026-03-12', 2400, 2600, 4.8, 111, 200, 41.67, 532.8),
(3, '2026-04-12', 2600, 2800, 5, 111, 200, 40, 555),
(3, '2026-05-12', 2800, 3000, 5.1, 112, 200, 39.22, 571.2),

(4, '2026-01-15', 8000, 8400, 30, 95, 400, 13.33, 2850),
(4, '2026-02-15', 8400, 8800, 32, 95, 400, 12.5, 3040),
(4, '2026-03-15', 8800, 9200, 28, 96, 400, 14.29, 2688),
(4, '2026-04-15', 9200, 9600, 30, 96, 400, 13.33, 2880),
(4, '2026-05-15', 9600, 10000, 31, 96, 400, 12.9, 2976),

(5, '2026-01-18', 3000, 3300, 18, 105, 300, 16.67, 1890),
(5, '2026-02-18', 3300, 3600, 17, 105, 300, 17.65, 1785),
(5, '2026-03-18', 3600, 3900, 19, 106, 300, 15.79, 2014),
(5, '2026-04-18', 3900, 4200, 18, 106, 300, 16.67, 1908),
(5, '2026-05-18', 4200, 4500, 20, 106, 300, 15, 2120);


-- 6. Check the vehicles
SELECT * FROM vehicles;


-- 7. Check the fuel entries
SELECT * FROM fuel_entries;


-- 8. Display fuel entries with vehicle names
SELECT
    vehicles.vehicle_name,
    vehicles.vehicle_number,
    fuel_entries.fuel_date,
    fuel_entries.distance,
    fuel_entries.fuel_litres,
    fuel_entries.mileage,
    fuel_entries.total_cost
FROM vehicles
JOIN fuel_entries
ON vehicles.vehicle_id = fuel_entries.vehicle_id;


-- 9. Total fuel expenses for each vehicle
SELECT
    vehicles.vehicle_name,
    SUM(fuel_entries.total_cost) AS total_fuel_expense
FROM vehicles
JOIN fuel_entries
ON vehicles.vehicle_id = fuel_entries.vehicle_id
GROUP BY vehicles.vehicle_id, vehicles.vehicle_name;


-- 10. Monthly fuel expenses
SELECT
    DATE_FORMAT(fuel_date, '%Y-%m') AS month,
    SUM(total_cost) AS monthly_expense
FROM fuel_entries
GROUP BY DATE_FORMAT(fuel_date, '%Y-%m')
ORDER BY month;


-- 11. Average mileage for each vehicle
SELECT
    vehicles.vehicle_name,
    ROUND(AVG(fuel_entries.mileage), 2) AS average_mileage
FROM vehicles
JOIN fuel_entries
ON vehicles.vehicle_id = fuel_entries.vehicle_id
GROUP BY vehicles.vehicle_id, vehicles.vehicle_name;



