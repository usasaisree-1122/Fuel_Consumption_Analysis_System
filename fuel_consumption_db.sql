-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: fuel_consumption_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `fuel_entries`
--

DROP TABLE IF EXISTS `fuel_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fuel_entries` (
  `entry_id` int NOT NULL AUTO_INCREMENT,
  `vehicle_id` int NOT NULL,
  `fuel_date` date NOT NULL,
  `previous_odometer` decimal(10,2) NOT NULL,
  `current_odometer` decimal(10,2) NOT NULL,
  `fuel_litres` decimal(10,2) NOT NULL,
  `price_per_litre` decimal(10,2) NOT NULL,
  `distance` decimal(10,2) DEFAULT NULL,
  `mileage` decimal(10,2) DEFAULT NULL,
  `total_cost` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`entry_id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `fuel_entries_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `fuel_entries`
--

LOCK TABLES `fuel_entries` WRITE;
/*!40000 ALTER TABLE `fuel_entries` DISABLE KEYS */;
INSERT INTO `fuel_entries` VALUES (1,1,'2026-01-05',1000.00,1150.00,3.00,110.00,150.00,50.00,330.00),(2,1,'2026-02-05',1150.00,1300.00,3.20,110.00,150.00,46.88,352.00),(3,1,'2026-03-05',1300.00,1450.00,3.10,110.00,150.00,48.39,341.00),(4,1,'2026-04-05',1450.00,1600.00,3.00,112.00,150.00,50.00,336.00),(5,1,'2026-05-05',1600.00,1750.00,3.30,112.00,150.00,45.45,369.60),(6,2,'2026-01-10',5000.00,5300.00,20.00,105.00,300.00,15.00,2100.00),(7,2,'2026-02-10',5300.00,5600.00,21.00,105.00,300.00,14.29,2205.00),(8,2,'2026-03-10',5600.00,5900.00,19.00,106.00,300.00,15.79,2014.00),(9,2,'2026-04-10',5900.00,6200.00,20.00,106.00,300.00,15.00,2120.00),(10,2,'2026-05-10',6200.00,6500.00,22.00,106.00,300.00,13.64,2332.00),(11,3,'2026-01-12',2000.00,2200.00,5.00,110.00,200.00,40.00,550.00),(12,3,'2026-02-12',2200.00,2400.00,5.20,110.00,200.00,38.46,572.00),(13,3,'2026-03-12',2400.00,2600.00,4.80,111.00,200.00,41.67,532.80),(14,3,'2026-04-12',2600.00,2800.00,5.00,111.00,200.00,40.00,555.00),(15,3,'2026-05-12',2800.00,3000.00,5.10,112.00,200.00,39.22,571.20),(16,4,'2026-01-15',8000.00,8400.00,30.00,95.00,400.00,13.33,2850.00),(17,4,'2026-02-15',8400.00,8800.00,32.00,95.00,400.00,12.50,3040.00),(18,4,'2026-03-15',8800.00,9200.00,28.00,96.00,400.00,14.29,2688.00),(19,4,'2026-04-15',9200.00,9600.00,30.00,96.00,400.00,13.33,2880.00),(20,4,'2026-05-15',9600.00,10000.00,31.00,96.00,400.00,12.90,2976.00),(21,5,'2026-01-18',3000.00,3300.00,18.00,105.00,300.00,16.67,1890.00),(22,5,'2026-02-18',3300.00,3600.00,17.00,105.00,300.00,17.65,1785.00),(23,5,'2026-03-18',3600.00,3900.00,19.00,106.00,300.00,15.79,2014.00),(24,5,'2026-04-18',3900.00,4200.00,18.00,106.00,300.00,16.67,1908.00),(25,5,'2026-05-18',4200.00,4500.00,20.00,106.00,300.00,15.00,2120.00);
/*!40000 ALTER TABLE `fuel_entries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vehicles`
--

DROP TABLE IF EXISTS `vehicles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vehicles` (
  `vehicle_id` int NOT NULL AUTO_INCREMENT,
  `vehicle_name` varchar(100) NOT NULL,
  `vehicle_number` varchar(20) NOT NULL,
  `vehicle_type` varchar(50) DEFAULT NULL,
  `fuel_type` varchar(30) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`vehicle_id`),
  UNIQUE KEY `vehicle_number` (`vehicle_number`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vehicles`
--

LOCK TABLES `vehicles` WRITE;
/*!40000 ALTER TABLE `vehicles` DISABLE KEYS */;
INSERT INTO `vehicles` VALUES (1,'Honda Activa','AP03AB1001','Scooter','Petrol','2026-10-25 05:18:48'),(2,'Hyundai i20','AP03CD2002','Car','Petrol','2026-10-25 05:18:48'),(3,'Royal Enfield Classic','AP03EF3003','Bike','Petrol','2026-10-25 05:18:48'),(4,'Tata Nexon','AP03GH4004','Car','Diesel','2026-10-25 05:18:48'),(5,'Maruti Swift','AP03IJ5005','Car','Petrol','2026-10-25 05:18:48');
/*!40000 ALTER TABLE `vehicles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-25 11:07:15
