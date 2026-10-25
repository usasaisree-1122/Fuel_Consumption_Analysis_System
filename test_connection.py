
import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aimlb2",
    database="fuel_consumption_db"
)

if connection.is_connected():
    print("Connected to MySQL successfully!")

connection.close()
print("Connection closed.")
