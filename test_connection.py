
from db_connection import get_connection

try:
    connection = get_connection()
    print("MySQL connected successfully!")

    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    result = cursor.fetchone()

    print("Total vehicles:", result[0])

    cursor.close()
    connection.close()

except Exception as error:
    print("Connection failed:", error)
