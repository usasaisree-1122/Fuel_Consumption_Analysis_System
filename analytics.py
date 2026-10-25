import mysql.connector
import pandas as pd
import numpy as np


# 1. Load fuel data from MySQL
def load_fuel_data():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="aimlb2",
        database="fuel_consumption_db"
    )

    query = """
        SELECT
            v.vehicle_id,
            v.vehicle_code,
            v.vehicle_type,
            v.fuel_type,
            f.record_id,
            f.fill_date,
            f.odometer_km,
            f.litres,
            f.total_cost,
            f.full_tank_flag
        FROM vehicles v
        JOIN fuel_records f
            ON v.vehicle_id = f.vehicle_id
        ORDER BY v.vehicle_code, f.fill_date, f.record_id
    """

    try:
        df = pd.read_sql(query, connection)
    finally:
        connection.close()

    return df


# 2. Clean and validate the data
def clean_fuel_data(df):
    df = df.copy()

    if df.empty:
        return df

    df["fill_date"] = pd.to_datetime(
        df["fill_date"], errors="coerce"
    )

    numeric_columns = [
        "odometer_km",
        "litres",
        "total_cost"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

    df = df.dropna(
        subset=[
            "vehicle_id",
            "vehicle_code",
            "fill_date",
            "odometer_km",
            "litres",
            "total_cost"
        ]
    )

    # Remove invalid fuel quantities and costs
    df = df[
        (df["litres"] > 0) &
        (df["total_cost"] >= 0) &
        (df["odometer_km"] >= 0)
    ].copy()

    # Convert full-tank values into Boolean values
    df["full_tank_flag"] = (
        df["full_tank_flag"]
        .astype(str)
        .str.lower()
        .isin(["1", "true", "yes"])
    )

    # Sort readings in chronological order
    df = df.sort_values(
        ["vehicle_id", "fill_date", "record_id"]
    ).reset_index(drop=True)

    # Remove readings where the odometer goes backwards
    df["previous_odometer"] = (
        df.groupby("vehicle_id")["odometer_km"].shift(1)
    )

    valid_odometer = (
        df["previous_odometer"].isna() |
        (
            df["odometer_km"] >=
            df["previous_odometer"]
        )
    )

    df = df[valid_odometer].copy()

    df = df.drop(
        columns=["previous_odometer"]
    ).reset_index(drop=True)

    return df


# 3. Calculate distance and approximate mileage
def calculate_mileage(df):
    df = df.copy()

    df = df.sort_values(
        ["vehicle_id", "fill_date", "record_id"]
    ).reset_index(drop=True)

    df["previous_odometer"] = (
        df.groupby("vehicle_id")["odometer_km"].shift(1)
    )

    df["distance_km"] = (
        df["odometer_km"] - df["previous_odometer"]
    )

    # The first reading for each vehicle has no previous distance
    df["distance_km"] = df["distance_km"].fillna(0)

    # Approximate mileage = distance travelled / litres added
    df["approx_mileage_km_per_litre"] = (
        df["distance_km"] /
        df["litres"].replace(0, np.nan)
    )

    # A zero-distance reading does not provide a mileage value
    df.loc[
        df["distance_km"] <= 0,
        "approx_mileage_km_per_litre"
    ] = np.nan

    return df


# 4. Calculate mileage using full-tank readings
def calculate_full_tank_mileage(df):
    df = df.copy()

    df = df.sort_values(
        ["vehicle_id", "fill_date", "record_id"]
    ).reset_index(drop=True)

    df["full_tank_mileage_km_per_litre"] = np.nan

    for vehicle_id in df["vehicle_id"].unique():
        vehicle_rows = df[
            df["vehicle_id"] == vehicle_id
        ]

        previous_full_tank_index = None

        for index in vehicle_rows.index:
            if bool(df.loc[index, "full_tank_flag"]):
                if previous_full_tank_index is not None:
                    start_odometer = df.loc[
                        previous_full_tank_index,
                        "odometer_km"
                    ]

                    end_odometer = df.loc[
                        index, "odometer_km"
                    ]

                    distance = end_odometer - start_odometer

                    # Include fuel added after the previous
                    # full-tank reading, up to this reading.
                    fuel_used_estimate = df.loc[
                        previous_full_tank_index + 1:index,
                        "litres"
                    ].sum()

                    if distance > 0 and fuel_used_estimate > 0:
                        df.loc[
                            index,
                            "full_tank_mileage_km_per_litre"
                        ] = (
                            distance / fuel_used_estimate
                        )

                previous_full_tank_index = index

    return df


# 5. Report total expenses for each vehicle
def vehicle_expense_report(df):
    report = (
        df.groupby(
            ["vehicle_code", "vehicle_type", "fuel_type"],
            as_index=False
        )
        .agg(
            total_fuel_litres=("litres", "sum"),
            total_expense=("total_cost", "sum")
        )
    )

    return report


# 6. Report monthly expenses and fuel consumption
def monthly_expense_report(df):
    df = df.copy()

    df["month"] = (
        pd.to_datetime(df["fill_date"])
        .dt.to_period("M")
        .astype(str)
    )

    report = (
        df.groupby(
            ["month", "vehicle_code"],
            as_index=False
        )
        .agg(
            total_fuel_litres=("litres", "sum"),
            total_expense=("total_cost", "sum")
        )
    )

    return report


# 7. Compare vehicles
def vehicle_comparison_report(df):
    df = df.copy()

    if "distance_km" not in df.columns:
        df = calculate_mileage(df)

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    # Only count refill costs against intervals with a positive distance.
    df["interval_expense"] = df["total_cost"].where(
        df["distance_km"] > 0, 0
    )

    report = (
        df.groupby(
            ["vehicle_code", "vehicle_type", "fuel_type"],
            as_index=False
        )
        .agg(
            total_distance_km=("distance_km", "sum"),
            total_fuel_litres=("litres", "sum"),
            average_approx_mileage=(
                "approx_mileage_km_per_litre", "mean"
            ),
            total_expense=("total_cost", "sum"),
            interval_expense=("interval_expense", "sum")
        )
    )

    report["overall_cost_per_km"] = (
        report["interval_expense"] /
        report["total_distance_km"].replace(0, np.nan)
    )

    report.replace(
        [np.inf, -np.inf], np.nan, inplace=True
    )

    return report


# 8. Compare expenses between two periods
def period_comparison_report(df, start_date, end_date):
    df = df.copy()

    df["fill_date"] = pd.to_datetime(
        df["fill_date"], errors="coerce"
    )

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    period_df = df[
        (df["fill_date"] >= start_date) &
        (df["fill_date"] <= end_date)
    ]

    report = (
        period_df.groupby(
            ["vehicle_code", "vehicle_type", "fuel_type"],
            as_index=False
        )
        .agg(
            total_fuel_litres=("litres", "sum"),
            total_expense=("total_cost", "sum")
        )
    )

    return report


# 9. Detect unusually high or low mileage
def detect_unusual_consumption(df, threshold=0.30):
    df = df.copy()

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    df["unusual_consumption"] = False

    for vehicle_id in df["vehicle_id"].unique():
        vehicle_rows = df[
            df["vehicle_id"] == vehicle_id
        ]

        valid_mileage = vehicle_rows[
            vehicle_rows[
                "approx_mileage_km_per_litre"
            ].notna()
        ][
            "approx_mileage_km_per_litre"
        ]

        # Need at least three valid readings for comparison
        if len(valid_mileage) < 3:
            continue

        median_mileage = valid_mileage.median()

        if median_mileage <= 0:
            continue

        lower_limit = median_mileage * (1 - threshold)
        upper_limit = median_mileage * (1 + threshold)

        unusual_rows = (
            vehicle_rows[
                "approx_mileage_km_per_litre"
            ].notna()
        ) & (
            (
                vehicle_rows[
                    "approx_mileage_km_per_litre"
                ] < lower_limit
            ) |
            (
                vehicle_rows[
                    "approx_mileage_km_per_litre"
                ] > upper_limit
            )
        )

        df.loc[
            vehicle_rows.index[unusual_rows],
            "unusual_consumption"
        ] = True

    return df


# 10. Prepare data for the teammate's charts
def prepare_chart_data(df):
    df = df.copy()

    if "distance_km" not in df.columns:
        df = calculate_mileage(df)

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    monthly_data = monthly_expense_report(df)
    vehicle_data = vehicle_comparison_report(df)

    return {
        "monthly_data": monthly_data,
        "vehicle_data": vehicle_data
    }


# 11. Run the project
if __name__ == "__main__":
    try:
        fuel_data = load_fuel_data()

        if fuel_data.empty:
            print("No fuel records found in the database.")

        else:
            fuel_data = clean_fuel_data(fuel_data)
            fuel_data = calculate_mileage(fuel_data)
            fuel_data = calculate_full_tank_mileage(fuel_data)
            fuel_data = detect_unusual_consumption(fuel_data)

            print("\n--- Fuel Records with Mileage ---")
            print(fuel_data)

            print("\n--- Vehicle Expense Report ---")
            print(vehicle_expense_report(fuel_data))

            print("\n--- Monthly Expense Report ---")
            print(monthly_expense_report(fuel_data))

            print("\n--- Vehicle Comparison Report ---")
            print(vehicle_comparison_report(fuel_data))

            print("\n--- Unusual Consumption Records ---")
            print(
                fuel_data[
                    fuel_data["unusual_consumption"]
                ]
            )

            chart_data = prepare_chart_data(fuel_data)

            print("\n--- Chart Data Prepared ---")
            print("Monthly data:")
            print(chart_data["monthly_data"])

            print("\nVehicle data:")
            print(chart_data["vehicle_data"])

    except mysql.connector.Error as error:
        print("Database error:", error)

    except Exception as error:
        print("Error:", error)