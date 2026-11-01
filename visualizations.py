
import os
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from db_connection import get_connection


BASE_IMAGE_DIR = os.path.join("static", "images")

COLUMNS = [
    "vehicle_name", "vehicle_number", "fuel_date",
    "distance", "fuel_litres", "price_per_litre",
    "mileage", "total_cost"
]


def load_chart_data(vehicle_ids=None):
    conn = get_connection()

    try:
        sql = """
            SELECT v.vehicle_name, v.vehicle_number, f.fuel_date,
                   f.distance, f.fuel_litres, f.price_per_litre,
                   f.mileage, f.total_cost
            FROM fuel_entries f
            JOIN vehicles v ON v.vehicle_id = f.vehicle_id
        """

        if vehicle_ids is not None:
            if not vehicle_ids:
                return pd.DataFrame(columns=COLUMNS)

            placeholders = ",".join(["%s"] * len(vehicle_ids))
            sql += f" WHERE f.vehicle_id IN ({placeholders})"

            return pd.read_sql(sql, conn, params=tuple(vehicle_ids))

        return pd.read_sql(sql, conn)

    finally:
        conn.close()


def save_chart(fig, filename, image_dir):
    fig.tight_layout()
    fig.savefig(
        os.path.join(image_dir, filename),
        dpi=150,
        bbox_inches="tight"
    )
    plt.close(fig)


def empty_chart(filename, title, image_dir):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.text(
        0.5, 0.5, "No data available yet",
        ha="center", va="center",
        transform=ax.transAxes
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")
    save_chart(fig, filename, image_dir)


def prepare_data(df):
    df = df.copy()

    for column in [
        "distance", "fuel_litres", "price_per_litre",
        "mileage", "total_cost"
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["fuel_date"] = pd.to_datetime(
        df["fuel_date"], errors="coerce"
    )

    return df


def mileage_comparison_chart(df, image_dir):
    filename = "mileage_comparison.png"

    valid = df.dropna(subset=["vehicle_name", "mileage"])
    valid = valid[valid["mileage"] > 0]

    if valid.empty:
        return empty_chart(filename, "Average Mileage by Vehicle", image_dir)

    values = valid.groupby("vehicle_name")["mileage"].mean().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax, label="Average Mileage")

    ax.set_title("Average Mileage by Vehicle")
    ax.set_xlabel("Vehicle Name")
    ax.set_ylabel("Mileage (km/L)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)

    save_chart(fig, filename, image_dir)


def monthly_expenses_chart(df, image_dir):
    filename = "monthly_expenses.png"

    valid = df.dropna(subset=["fuel_date", "total_cost"]).copy()

    if valid.empty:
        return empty_chart(filename, "Monthly Fuel Expenses", image_dir)

    valid["month"] = valid["fuel_date"].dt.to_period("M").astype(str)
    values = valid.groupby("month")["total_cost"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(
        values.index, values.values,
        marker="o", label="Monthly Fuel Cost"
    )

    ax.set_title("Monthly Fuel Expenses")
    ax.set_xlabel("Month")
    ax.set_ylabel("Expense (₹)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(alpha=0.25)

    save_chart(fig, filename, image_dir)


def fuel_consumption_chart(df, image_dir):
    filename = "fuel_consumption.png"

    valid = df.dropna(subset=["vehicle_name", "fuel_litres"])

    if valid.empty:
        return empty_chart(filename, "Fuel Consumption by Vehicle", image_dir)

    values = valid.groupby("vehicle_name")["fuel_litres"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax, label="Total Fuel Used")

    ax.set_title("Total Fuel Consumption by Vehicle")
    ax.set_xlabel("Vehicle Name")
    ax.set_ylabel("Fuel Used (Litres)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)

    save_chart(fig, filename, image_dir)


def cost_per_kilometre_chart(df, image_dir):
    filename = "cost_per_kilometre.png"

    valid = df.dropna(
        subset=["vehicle_name", "distance", "total_cost"]
    )
    valid = valid[
        (valid["distance"] > 0) & (valid["total_cost"] >= 0)
    ]

    if valid.empty:
        return empty_chart(filename, "Fuel Cost per Kilometre", image_dir)

    distance = valid.groupby("vehicle_name")["distance"].sum()
    cost = valid.groupby("vehicle_name")["total_cost"].sum()
    values = (cost / distance).dropna().sort_values()

    if values.empty:
        return empty_chart(filename, "Fuel Cost per Kilometre", image_dir)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax, label="Average Cost per KM")

    ax.set_title("Fuel Cost per Kilometre by Vehicle")
    ax.set_xlabel("Vehicle Name")
    ax.set_ylabel("Fuel Cost (₹/km)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)

    save_chart(fig, filename, image_dir)


def monthly_consumption_chart(df, image_dir):
    filename = "monthly_consumption.png"

    valid = df.dropna(subset=["fuel_date", "fuel_litres"]).copy()

    if valid.empty:
        return empty_chart(filename, "Monthly Fuel Consumption", image_dir)

    valid["month"] = valid["fuel_date"].dt.to_period("M").astype(str)
    values = valid.groupby("month")["fuel_litres"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(
        values.index, values.values,
        marker="o", label="Monthly Fuel Used"
    )

    ax.set_title("Monthly Fuel Consumption")
    ax.set_xlabel("Month")
    ax.set_ylabel("Fuel Used (Litres)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(alpha=0.25)

    save_chart(fig, filename, image_dir)


def vehicle_performance_chart(df, image_dir):
    filename = "vehicle_performance.png"

    valid = df.dropna(subset=["vehicle_name", "distance"])
    valid = valid[valid["distance"] > 0]

    if valid.empty:
        return empty_chart(filename, "Distance Travelled by Vehicle", image_dir)

    values = valid.groupby("vehicle_name")["distance"].sum().sort_values()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    values.plot(kind="bar", ax=ax, label="Total Distance")

    ax.set_title("Total Distance Travelled by Vehicle")
    ax.set_xlabel("Vehicle Name")
    ax.set_ylabel("Distance (km)")
    ax.legend(title="Legend")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)

    save_chart(fig, filename, image_dir)


def generate_all_charts(vehicle_ids=None, chart_key="default"):
    """
    Generate charts using only the supplied vehicle IDs.
    Each user gets a separate image folder.
    """

    image_dir = os.path.join(BASE_IMAGE_DIR, chart_key)
    os.makedirs(image_dir, exist_ok=True)

    df = load_chart_data(vehicle_ids)
    df = prepare_data(df)

    mileage_comparison_chart(df, image_dir)
    monthly_expenses_chart(df, image_dir)
    fuel_consumption_chart(df, image_dir)
    cost_per_kilometre_chart(df, image_dir)
    monthly_consumption_chart(df, image_dir)
    vehicle_performance_chart(df, image_dir)

    return [
        f"{chart_key}/mileage_comparison.png",
        f"{chart_key}/monthly_expenses.png",
        f"{chart_key}/fuel_consumption.png",
        f"{chart_key}/cost_per_kilometre.png",
        f"{chart_key}/monthly_consumption.png",
        f"{chart_key}/vehicle_performance.png"
    ]
