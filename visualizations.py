import matplotlib.pyplot as plt
import mysql.connector
import pandas as pd

from db_connection import get_connection

def get_mileage_data():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            v.vehicle_name,
            AVG(f.mileage) AS average_mileage
        FROM vehicles v
        JOIN fuel_entries f
            ON v.vehicle_id = f.vehicle_id
        GROUP BY v.vehicle_id, v.vehicle_name
        ORDER BY v.vehicle_name
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        return df

    finally:
        cursor.close()
        connection.close()

def plot_mileage_comparison():
    df = get_mileage_data()

    if df.empty:
        print("No mileage data available.")
        return

    plt.figure(figsize=(10, 5))

    plt.bar(
        df["vehicle_name"],
        df["average_mileage"]
    )

    plt.title("Average Mileage Comparison by Vehicle")
    plt.xlabel("Vehicle Name")
    plt.ylabel("Average Mileage (km/litre)")
    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig("static/images/mileage_comparison.png")
    plt.close()


def get_monthly_expenses():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            DATE_FORMAT(fuel_date, '%Y-%m') AS month,
            SUM(total_cost) AS monthly_expense
        FROM fuel_entries
        GROUP BY DATE_FORMAT(fuel_date, '%Y-%m')
        ORDER BY month
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return pd.DataFrame(rows)
    finally:
        cursor.close()
        connection.close()


def plot_monthly_expenses():
    df = get_monthly_expenses()

    if df.empty:
        print("No expense data available.")
        return

    plt.figure(figsize=(10, 5))
    plt.bar(df["month"], df["monthly_expense"])

    plt.title("Monthly Fuel Expenses")
    plt.xlabel("Month")
    plt.ylabel("Total Expense")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("static/images/monthly_expenses.png")
    plt.close()

def get_fuel_consumption_data():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            v.vehicle_name,
            SUM(f.fuel_litres) AS total_litres
        FROM vehicles v
        JOIN fuel_entries f
            ON v.vehicle_id = f.vehicle_id
        GROUP BY v.vehicle_id, v.vehicle_name
        ORDER BY v.vehicle_name
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return pd.DataFrame(rows)
    finally:
        cursor.close()
        connection.close()


def plot_fuel_consumption():
    df = get_fuel_consumption_data()

    if df.empty:
        print("No fuel consumption data available.")
        return

    plt.figure(figsize=(10, 5))
    plt.bar(df["vehicle_name"], df["total_litres"])

    plt.title("Total Fuel Consumption by Vehicle")
    plt.xlabel("Vehicle Name")
    plt.ylabel("Total Fuel Consumed (Litres)")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("static/images/fuel_consumption.png")
    plt.close()


def plot_vehicle_performance():
    df = get_mileage_data()

    if df.empty:
        print("No mileage data available.")
        return

    df = df.sort_values(
        by="average_mileage",
        ascending=False
    )

    plt.figure(figsize=(10, 5))
    plt.bar(
        df["vehicle_name"],
        df["average_mileage"]
    )

    plt.title("Vehicle Fuel Efficiency Performance")
    plt.xlabel("Vehicle Name")
    plt.ylabel("Average Mileage (km/litre)")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig("static/images/vehicle_performance.png")
    plt.close()

if __name__ == "__main__":
    print("Fuel Consumption Analysis System")
    print("1. Mileage Comparison")
    print("2. Monthly Fuel Expenses")
    print("3. Fuel Consumption")
    print("4. Vehicle Performance")

    choice = input("Choose a chart (1-4): ")

    if choice == "1":
        plot_mileage_comparison()
    elif choice == "2":
        plot_monthly_expenses()
    elif choice == "3":
        plot_fuel_consumption()
    elif choice == "4":
        plot_vehicle_performance()
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")