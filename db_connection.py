
import mysql.connector
def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="aimlb2",
        database="fuel_consumption_db"
    )
    return connection
