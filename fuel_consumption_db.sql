DROP DATABASE IF EXISTS fuel_consumption_db;

CREATE DATABASE fuel_consumption_db;

USE fuel_consumption_db;

-- 1. USERS TABLE
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM(
        'individual_owner',
        'fleet_manager',
        'staff'
    ) NOT NULL DEFAULT 'individual_owner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. VEHICLES TABLE
CREATE TABLE vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_name VARCHAR(100) NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50),
    fuel_type VARCHAR(30),
    owner_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

-- 3. FUEL ENTRIES TABLE
CREATE TABLE fuel_entries (
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
    full_tank_flag BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE CASCADE,

    FOREIGN KEY (created_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL,

    CHECK (fuel_litres > 0),
    CHECK (current_odometer > previous_odometer),

    INDEX idx_fuel_vehicle_date (vehicle_id, fuel_date)
);

-- 4. INVALID READINGS TABLE
CREATE TABLE invalid_readings (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NULL,
    entered_date DATE NULL,
    previous_odometer DECIMAL(10,2),
    current_odometer DECIMAL(10,2),
    fuel_litres DECIMAL(10,2),
    reason VARCHAR(255) NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE SET NULL
);

-- 5. STAFF ASSIGNMENTS TABLE
CREATE TABLE staff_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    staff_user_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    assigned_by INT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_staff_vehicle (
        staff_user_id,
        vehicle_id
    ),

    FOREIGN KEY (staff_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE CASCADE,

    FOREIGN KEY (assigned_by)
        REFERENCES users(user_id)
        ON DELETE SET NULL
);

-- 6. SAMPLE VEHICLES
INSERT INTO vehicles
(vehicle_name, vehicle_number, vehicle_type, fuel_type)
VALUES
('Honda Activa', 'AP03AB1001', 'Scooter', 'Petrol'),
('Hyundai i20', 'AP03CD2002', 'Car', 'Petrol'),
('Royal Enfield Classic', 'AP03EF3003', 'Bike', 'Petrol'),
('Tata Nexon', 'AP03GH4004', 'Car', 'Diesel'),
('Maruti Swift', 'AP03IJ5005', 'Car', 'Petrol');

-- 7. SAMPLE FUEL ENTRIES
INSERT INTO fuel_entries
(vehicle_id, fuel_date, previous_odometer,
 current_odometer, fuel_litres, price_per_litre,
 distance, mileage, total_cost, full_tank_flag)
VALUES
(1,'2026-01-05',1000,1150,3,110,150,50,330,TRUE),
(1,'2026-02-05',1150,1300,3.2,110,150,46.88,352,TRUE),
(1,'2026-03-05',1300,1450,3.1,110,150,48.39,341,TRUE),
(1,'2026-04-05',1450,1600,3,112,150,50,336,TRUE),
(1,'2026-05-05',1600,1750,3.3,112,150,45.45,369.6,TRUE),

(2,'2026-01-10',5000,5300,20,105,300,15,2100,TRUE),
(2,'2026-02-10',5300,5600,21,105,300,14.29,2205,TRUE),
(2,'2026-03-10',5600,5900,19,106,300,15.79,2014,TRUE),
(2,'2026-04-10',5900,6200,20,106,300,15,2120,TRUE),
(2,'2026-05-10',6200,6500,22,106,300,13.64,2332,TRUE),

(3,'2026-01-12',2000,2200,5,110,200,40,550,TRUE),
(3,'2026-02-12',2200,2400,5.2,110,200,38.46,572,TRUE),
(3,'2026-03-12',2400,2600,4.8,111,200,41.67,532.8,TRUE),
(3,'2026-04-12',2600,2800,5,111,200,40,555,TRUE),
(3,'2026-05-12',2800,3000,5.1,112,200,39.22,571.2,TRUE),

(4,'2026-01-15',8000,8400,30,95,400,13.33,2850,TRUE),
(4,'2026-02-15',8400,8800,32,95,400,12.5,3040,TRUE),
(4,'2026-03-15',8800,9200,28,96,400,14.29,2688,TRUE),
(4,'2026-04-15',9200,9600,30,96,400,13.33,2880,TRUE),
(4,'2026-05-15',9600,10000,31,96,400,12.9,2976,TRUE),

(5,'2026-01-18',3000,3300,18,105,300,16.67,1890,TRUE),
(5,'2026-02-18',3300,3600,17,105,300,17.65,1785,TRUE),
(5,'2026-03-18',3600,3900,19,106,300,15.79,2014,TRUE),
(5,'2026-04-18',3900,4200,18,106,300,16.67,1908,TRUE),
(5,'2026-05-18',4200,4500,20,106,300,15,2120,TRUE);

-- 8. VERIFY DATABASE
SHOW TABLES;

SELECT * FROM vehicles;
SELECT * FROM fuel_entries;
SELECT * FROM users;
SELECT * FROM invalid_readings;
SELECT * FROM staff_assignments;