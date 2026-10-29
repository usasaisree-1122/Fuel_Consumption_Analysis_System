
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from db_connection import get_connection

IMAGE_DIR = os.path.join("static", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)


def load_chart_data():
    conn = get_connection()
    try:
        sql = """
            SELECT v.vehicle_name, v.vehicle_number, f.fuel_date,
                   f.distance, f.fuel_litres, f.price_per_litre,
                   f.mileage, f.total_cost
            FROM fuel_entries f
            JOIN vehicles v ON v.vehicle_id = f.vehicle_id
            ORDER BY f.fuel_date, f.entry_id
        """
        return pd.read_sql(sql, conn)
    finally:
        conn.close()


def save_chart(fig, filename):
    fig.tight_layout()
    fig.savefig(
        os.path.join(IMAGE_DIR, filename),
        dpi=150,
        bbox_inches="tight"
    )
    plt.close(fig)


def empty_chart(filename, title):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.text(
        0.5, 0.5, "No data available yet",
        ha="center", va="center",
        transform=ax.transAxes
    )
    ax.set_title(title)
    ax.axis("off")
    save_chart(fig, filename)


def mileage_comparison_chart(df):
    filename = "mileage_comparison.png"
    valid = df[
        df["mileage"].notna() & (df["mileage"] > 0)
    ] if not df.empty else df

    if valid.empty:
        return empty_chart(filename, "Average Mileage by Vehicle")

    values = valid.groupby("vehicle_name")["mileage"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax)
    ax.set_title("Average Mileage by Vehicle")
    ax.set_xlabel("Vehicle")
    ax.set_ylabel("Mileage (km/L)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    save_chart(fig, filename)


def monthly_expenses_chart(df):
    filename = "monthly_expenses.png"
    if df.empty:
        return empty_chart(filename, "Monthly Fuel Expenses")

    df = df.copy()
    df["fuel_date"] = pd.to_datetime(df["fuel_date"], errors="coerce")
    df = df.dropna(subset=["fuel_date"])

    if df.empty:
        return empty_chart(filename, "Monthly Fuel Expenses")

    df["month"] = df["fuel_date"].dt.to_period("M").astype(str)
    values = df.groupby("month")["total_cost"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(values.index, values.values, marker="o")
    ax.set_title("Monthly Fuel Expenses")
    ax.set_xlabel("Month")
    ax.set_ylabel("Expense (₹)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(alpha=0.25)
    save_chart(fig, filename)


def fuel_consumption_chart(df):
    filename = "fuel_consumption.png"
    if df.empty:
        return empty_chart(filename, "Fuel Consumption by Vehicle")

    values = df.groupby("vehicle_name")["fuel_litres"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax)
    ax.set_title("Total Fuel Consumption by Vehicle")
    ax.set_xlabel("Vehicle")
    ax.set_ylabel("Fuel used (litres)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    save_chart(fig, filename)


def cost_per_kilometre_chart(df):
    filename = "cost_per_kilometre.png"
    valid = df[
        (df["distance"] > 0) & (df["total_cost"] >= 0)
    ] if not df.empty else df

    if valid.empty:
        return empty_chart(filename, "Fuel Cost per Kilometre")

    distance = valid.groupby("vehicle_name")["distance"].sum()
    cost = valid.groupby("vehicle_name")["total_cost"].sum()
    values = (cost / distance).dropna().sort_values()

    if values.empty:
        return empty_chart(filename, "Fuel Cost per Kilometre")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax)
    ax.set_title("Fuel Cost per Kilometre by Vehicle")
    ax.set_xlabel("Vehicle")
    ax.set_ylabel("Fuel cost (₹/km)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    save_chart(fig, filename)


def monthly_consumption_chart(df):
    filename = "monthly_consumption.png"
    if df.empty:
        return empty_chart(filename, "Monthly Fuel Consumption")

    df = df.copy()
    df["fuel_date"] = pd.to_datetime(df["fuel_date"], errors="coerce")
    df = df.dropna(subset=["fuel_date"])

    if df.empty:
        return empty_chart(filename, "Monthly Fuel Consumption")

    df["month"] = df["fuel_date"].dt.to_period("M").astype(str)
    values = df.groupby("month")["fuel_litres"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(values.index, values.values, marker="o")
    ax.set_title("Monthly Fuel Consumption")
    ax.set_xlabel("Month")
    ax.set_ylabel("Fuel used (litres)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(alpha=0.25)
    save_chart(fig, filename)


def vehicle_performance_chart(df):
    # Different from mileage: this compares total distance travelled.
    filename = "vehicle_performance.png"
    valid = df[df["distance"] > 0] if not df.empty else df

    if valid.empty:
        return empty_chart(filename, "Distance Travelled by Vehicle")

    values = valid.groupby("vehicle_name")["distance"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax)
    ax.set_title("Total Distance Travelled by Vehicle")
    ax.set_xlabel("Vehicle")
    ax.set_ylabel("Distance (km)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    save_chart(fig, filename)


def generate_all_charts():
    df = load_chart_data()

    mileage_comparison_chart(df)
    monthly_expenses_chart(df)
    fuel_consumption_chart(df)
    cost_per_kilometre_chart(df)
    monthly_consumption_chart(df)
    vehicle_performance_chart(df)


if __name__ == "__main__":
    generate_all_charts()
    print("All six charts generated in static/images/")
