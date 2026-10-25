
import numpy as np
import pandas as pd

from db_connection import get_connection


# 1. Load fuel data from the existing MySQL database
def load_fuel_data():
    connection = get_connection()

    query = """
        SELECT
            v.vehicle_id,
            v.vehicle_name,
            v.vehicle_type,
            v.fuel_type,
            f.entry_id,
            f.fuel_date,
            f.previous_odometer,
            f.current_odometer,
            f.fuel_litres,
            f.price_per_litre,
            f.total_cost,
            f.distance,
            f.mileage
        FROM vehicles v
        JOIN fuel_entries f
            ON v.vehicle_id = f.vehicle_id
        ORDER BY v.vehicle_id, f.fuel_date, f.entry_id
    """

    try:
        return pd.read_sql_query(query, connection)
    finally:
        connection.close()


# 2. Clean and validate fuel data
def clean_fuel_data(df):
    df = df.copy()

    if df.empty:
        return df

    df["fuel_date"] = pd.to_datetime(
        df["fuel_date"], errors="coerce"
    )

    numeric_columns = [
        "vehicle_id",
        "entry_id",
        "previous_odometer",
        "current_odometer",
        "fuel_litres",
        "price_per_litre",
        "total_cost",
        "distance",
        "mileage"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    required_columns = [
        "vehicle_id",
        "entry_id",
        "vehicle_name",
        "fuel_date",
        "previous_odometer",
        "current_odometer",
        "fuel_litres",
        "price_per_litre"
    ]

    df = df.dropna(subset=required_columns)

    # Remove invalid readings and non-finite numbers
    for column in numeric_columns:
        if column in df.columns:
            df = df[
                np.isfinite(df[column].fillna(0))
            ].copy()

    df = df[
        (df["previous_odometer"] >= 0) &
        (df["current_odometer"] >= df["previous_odometer"]) &
        (df["fuel_litres"] > 0) &
        (df["price_per_litre"] >= 0)
    ].copy()

    # Recalculate derived values consistently
    df["distance"] = (
        df["current_odometer"] - df["previous_odometer"]
    )

    df["total_cost"] = (
        df["fuel_litres"] * df["price_per_litre"]
    )

    df["mileage"] = np.where(
        df["distance"] > 0,
        df["distance"] / df["fuel_litres"],
        np.nan
    )

    return df.sort_values(
        ["vehicle_id", "fuel_date", "entry_id"]
    ).reset_index(drop=True)


# 3. Calculate distance and approximate mileage
def calculate_mileage(df):
    df = df.copy()

    df["distance_km"] = (
        df["current_odometer"] - df["previous_odometer"]
    )

    df["approx_mileage_km_per_litre"] = np.nan

    valid_rows = (
        (df["distance_km"] > 0) &
        (df["fuel_litres"] > 0)
    )

    df.loc[
        valid_rows, "approx_mileage_km_per_litre"
    ] = (
        df.loc[valid_rows, "distance_km"] /
        df.loc[valid_rows, "fuel_litres"]
    )

    return df


# 4. Calculate full-tank mileage when that data is available
def calculate_full_tank_mileage(df):
    df = df.copy()

    df["full_tank_mileage_km_per_litre"] = np.nan

    # The existing database schema has no full-tank flag.
    # Do not invent full-tank results when the flag is missing.
    if "full_tank_flag" not in df.columns:
        return df

    df = df.sort_values(
        ["vehicle_id", "fuel_date", "entry_id"]
    ).reset_index(drop=True)

    for vehicle_id, group in df.groupby("vehicle_id", sort=False):
        previous_full_tank = None

        for idx in group.index:
            is_full_tank = (
                str(df.at[idx, "full_tank_flag"]).strip().lower()
                in {"1", "true", "yes"}
            )

            if not is_full_tank:
                continue

            if previous_full_tank is not None:
                start_odometer = df.at[
                    previous_full_tank, "current_odometer"
                ]
                end_odometer = df.at[idx, "current_odometer"]

                # Use positional rows between full-tank readings,
                # not arithmetic on DataFrame index labels.
                positions = list(group.index)
                start_pos = positions.index(previous_full_tank)
                end_pos = positions.index(idx)

                interval_indices = positions[
                    start_pos + 1:end_pos + 1
                ]

                fuel_used_estimate = df.loc[
                    interval_indices, "fuel_litres"
                ].sum()

                distance = end_odometer - start_odometer

                if distance > 0 and fuel_used_estimate > 0:
                    df.at[
                        idx, "full_tank_mileage_km_per_litre"
                    ] = distance / fuel_used_estimate

            previous_full_tank = idx

    return df


# 5. Total expenses for each vehicle
def vehicle_expense_report(df):
    return (
        df.groupby(
            ["vehicle_name", "vehicle_type", "fuel_type"],
            dropna=False,
            as_index=False
        )
        .agg(
            total_fuel_litres=("fuel_litres", "sum"),
            total_expense=("total_cost", "sum"),
            total_distance_km=("distance_km", "sum")
            if "distance_km" in df.columns
            else ("distance", "sum")
        )
    )


# 6. Monthly expenses and fuel consumption
def monthly_expense_report(df):
    df = df.copy()

    df["month"] = (
        pd.to_datetime(df["fuel_date"])
        .dt.to_period("M")
        .astype(str)
    )

    return (
        df.groupby(
            ["month", "vehicle_name"],
            as_index=False
        )
        .agg(
            total_fuel_litres=("fuel_litres", "sum"),
            total_expense=("total_cost", "sum")
        )
        .sort_values(["month", "vehicle_name"])
        .reset_index(drop=True)
    )


# 7. Compare vehicle performance and costs
def vehicle_comparison_report(df):
    df = df.copy()

    if "distance_km" not in df.columns:
        df = calculate_mileage(df)

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    report = (
        df.groupby(
            ["vehicle_name", "vehicle_type", "fuel_type"],
            dropna=False,
            as_index=False
        )
        .agg(
            total_distance_km=("distance_km", "sum"),
            total_fuel_litres=("fuel_litres", "sum"),
            average_approx_mileage=(
                "approx_mileage_km_per_litre", "mean"
            ),
            total_expense=("total_cost", "sum")
        )
    )

    report["overall_cost_per_km"] = (
        report["total_expense"] /
        report["total_distance_km"].replace(0, np.nan)
    )

    report.replace(
        [np.inf, -np.inf], np.nan, inplace=True
    )

    return report


# 8. Compare expenses within an inclusive date range
def period_comparison_report(df, start_date, end_date):
    df = df.copy()

    start_date = pd.to_datetime(
        start_date, errors="raise"
    ).normalize()

    end_date = pd.to_datetime(
        end_date, errors="raise"
    ).normalize()

    if start_date > end_date:
        raise ValueError(
            "Start date must be on or before end date"
        )

    df["fuel_date"] = pd.to_datetime(
        df["fuel_date"], errors="coerce"
    )

    # Include all times on the selected end date.
    period_df = df[
        (df["fuel_date"] >= start_date) &
        (df["fuel_date"] < end_date + pd.Timedelta(days=1))
    ]

    return (
        period_df.groupby(
            ["vehicle_name", "vehicle_type", "fuel_type"],
            dropna=False,
            as_index=False
        )
        .agg(
            total_fuel_litres=("fuel_litres", "sum"),
            total_expense=("total_cost", "sum")
        )
    )


# 9. Detect unusually high or low mileage
def detect_unusual_consumption(df, threshold=0.30):
    if not isinstance(threshold, (int, float)) or isinstance(
        threshold, bool
    ):
        raise ValueError("Threshold must be a number")

    if not np.isfinite(threshold) or not 0 <= threshold < 1:
        raise ValueError("Threshold must be at least 0 and less than 1")

    df = df.copy()

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    df["unusual_consumption"] = False

    for _, group in df.groupby("vehicle_id"):
        valid = group[
            group["approx_mileage_km_per_litre"].notna()
        ]

        # At least three readings are needed for comparison.
        if len(valid) < 3:
            continue

        median_mileage = valid[
            "approx_mileage_km_per_litre"
        ].median()

        if not np.isfinite(median_mileage) or median_mileage <= 0:
            continue

        lower_limit = median_mileage * (1 - threshold)
        upper_limit = median_mileage * (1 + threshold)

        unusual = (
            (valid["approx_mileage_km_per_litre"] < lower_limit) |
            (valid["approx_mileage_km_per_litre"] > upper_limit)
        )

        df.loc[valid.index[unusual], "unusual_consumption"] = True

    return df


# 10. Prepare data for Matplotlib charts
def prepare_chart_data(df):
    df = df.copy()

    if "distance_km" not in df.columns:
        df = calculate_mileage(df)

    if "approx_mileage_km_per_litre" not in df.columns:
        df = calculate_mileage(df)

    return {
        "monthly_data": monthly_expense_report(df),
        "vehicle_data": vehicle_comparison_report(df)
    }


# 11. Run analytics directly for testing
if __name__ == "__main__":
    try:
        fuel_data = load_fuel_data()
        fuel_data = clean_fuel_data(fuel_data)

        if fuel_data.empty:
            print("No valid fuel records found.")
        else:
            fuel_data = calculate_mileage(fuel_data)
            fuel_data = calculate_full_tank_mileage(fuel_data)
            fuel_data = detect_unusual_consumption(fuel_data)

            print("\n--- Fuel Records ---")
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

    except Exception as error:
        print("Analytics error:", error)
