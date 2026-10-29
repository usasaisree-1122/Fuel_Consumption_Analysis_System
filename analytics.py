
import numpy as np
import pandas as pd

from db_connection import get_connection


# ---------- LOAD DATA ----------

def load_fuel_data():
    """Load fuel records together with vehicle details."""
    connection = get_connection()

    try:
        query = """
            SELECT
                f.entry_id,
                f.vehicle_id,
                v.vehicle_name,
                v.vehicle_number,
                v.vehicle_type,
                v.fuel_type,
                f.fuel_date,
                f.previous_odometer,
                f.current_odometer,
                f.fuel_litres,
                f.price_per_litre,
                f.distance,
                f.mileage,
                f.total_cost
            FROM fuel_entries f
            JOIN vehicles v
                ON f.vehicle_id = v.vehicle_id
            ORDER BY f.fuel_date, f.entry_id
        """

        return pd.read_sql(query, connection)

    finally:
        connection.close()


# ---------- CLEAN DATA ----------

def clean_fuel_data(data):
    """Convert data types and remove invalid rows for analysis."""
    if data is None:
        return pd.DataFrame()

    df = data.copy()

    if df.empty:
        return df

    numeric_columns = [
        "previous_odometer",
        "current_odometer",
        "fuel_litres",
        "price_per_litre",
        "distance",
        "mileage",
        "total_cost"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    if "fuel_date" in df.columns:
        df["fuel_date"] = pd.to_datetime(
            df["fuel_date"], errors="coerce"
        )

    # Replace infinity with missing values.
    df = df.replace([np.inf, -np.inf], np.nan)

    required_columns = [
        "fuel_litres",
        "price_per_litre",
        "distance",
        "total_cost"
    ]

    for column in required_columns:
        if column not in df.columns:
            return pd.DataFrame()

    # Fuel quantity, price and distance must be positive.
    df = df[
        (df["fuel_litres"] > 0)
        & (df["price_per_litre"] > 0)
        & (df["distance"] > 0)
        & (df["total_cost"] >= 0)
    ].copy()

    # When odometer readings are present, validate their order.
    if (
        "previous_odometer" in df.columns
        and "current_odometer" in df.columns
    ):
        df = df[
            df["current_odometer"] > df["previous_odometer"]
        ].copy()

    if "fuel_date" in df.columns:
        df = df.dropna(subset=["fuel_date"])

    # Recalculate mileage consistently from distance and litres.
    df["mileage"] = df["distance"] / df["fuel_litres"]

    return df.reset_index(drop=True)


# ---------- MILEAGE ----------

def calculate_mileage(data):
    """Add a mileage column calculated from distance and litres."""
    if data is None:
        return pd.DataFrame()

    df = data.copy()

    if df.empty:
        return df

    if not {"distance", "fuel_litres"}.issubset(df.columns):
        return df

    distance = pd.to_numeric(df["distance"], errors="coerce")
    litres = pd.to_numeric(df["fuel_litres"], errors="coerce")

    valid = (
        distance.notna()
        & litres.notna()
        & np.isfinite(distance)
        & np.isfinite(litres)
        & (distance >= 0)
        & (litres > 0)
    )

    df["mileage"] = np.nan
    df.loc[valid, "mileage"] = (
        distance[valid] / litres[valid]
    )

    return df


def calculate_full_tank_mileage(data):
    """
    Calculate full-tank mileage only if full_tank_flag exists.

    Without a full-tank indicator, return NaN because the
    available records cannot reliably identify full-tank trips.
    """
    if data is None:
        return np.nan

    if "full_tank_flag" not in data.columns:
        return np.nan

    df = data.copy()

    if df.empty:
        return np.nan

    full_tank = df[
        df["full_tank_flag"].astype(str).str.lower().isin(
            ["1", "true", "yes"]
        )
    ]

    if full_tank.empty:
        return np.nan

    if not {"distance", "fuel_litres"}.issubset(full_tank.columns):
        return np.nan

    distance = pd.to_numeric(
        full_tank["distance"], errors="coerce"
    )
    litres = pd.to_numeric(
        full_tank["fuel_litres"], errors="coerce"
    )

    valid = (
        distance.notna()
        & litres.notna()
        & (distance >= 0)
        & (litres > 0)
    )

    if not valid.any():
        return np.nan

    return float(distance[valid].sum() / litres[valid].sum())


# ---------- VEHICLE EXPENSE REPORT ----------

def vehicle_expense_report(data):
    """Summarise fuel cost and usage for each vehicle."""
    if data is None or data.empty:
        return pd.DataFrame()

    required = {"vehicle_name", "total_cost", "fuel_litres"}
    if not required.issubset(data.columns):
        return pd.DataFrame()

    df = data.copy()

    if "distance" not in df.columns:
        df["distance"] = 0

    report = df.groupby("vehicle_name", as_index=False).agg(
        total_expense=("total_cost", "sum"),
        total_fuel_litres=("fuel_litres", "sum"),
        total_distance=("distance", "sum")
    )

    report["cost_per_km"] = np.where(
        report["total_distance"] > 0,
        report["total_expense"] / report["total_distance"],
        np.nan
    )

    return report.sort_values(
        "total_expense", ascending=False
    ).reset_index(drop=True)


# ---------- MONTHLY EXPENSE REPORT ----------

def monthly_expense_report(data):
    """Summarise fuel expenses month by month."""
    if data is None or data.empty:
        return pd.DataFrame()

    if not {"fuel_date", "total_cost"}.issubset(data.columns):
        return pd.DataFrame()

    df = data.copy()
    df["fuel_date"] = pd.to_datetime(
        df["fuel_date"], errors="coerce"
    )
    df["total_cost"] = pd.to_numeric(
        df["total_cost"], errors="coerce"
    )

    df = df.dropna(subset=["fuel_date", "total_cost"])

    if df.empty:
        return pd.DataFrame()

    df["month"] = df["fuel_date"].dt.to_period("M").astype(str)

    report = df.groupby("month", as_index=False).agg(
        total_expense=("total_cost", "sum")
    )

    return report.sort_values("month").reset_index(drop=True)


# ---------- VEHICLE COMPARISON ----------

def vehicle_comparison_report(data):
    """Compare mileage, distance and fuel usage by vehicle."""
    if data is None or data.empty:
        return pd.DataFrame()

    required = {"vehicle_name", "distance", "fuel_litres"}
    if not required.issubset(data.columns):
        return pd.DataFrame()

    df = data.copy()

    df["distance"] = pd.to_numeric(
        df["distance"], errors="coerce"
    )
    df["fuel_litres"] = pd.to_numeric(
        df["fuel_litres"], errors="coerce"
    )

    report = df.groupby("vehicle_name", as_index=False).agg(
        total_distance=("distance", "sum"),
        total_fuel_litres=("fuel_litres", "sum")
    )

    report["average_mileage"] = np.where(
        report["total_fuel_litres"] > 0,
        report["total_distance"] / report["total_fuel_litres"],
        np.nan
    )

    return report.sort_values(
        "average_mileage", ascending=False, na_position="last"
    ).reset_index(drop=True)


# ---------- PERIOD COMPARISON ----------

def period_comparison_report(data):
    """Compare total fuel expense in the latest two months."""
    monthly = monthly_expense_report(data)

    if monthly.empty:
        return pd.DataFrame(
            columns=["month", "total_expense", "change"]
        )

    monthly = monthly.tail(2).copy()
    monthly["change"] = monthly["total_expense"].diff()

    return monthly.reset_index(drop=True)


# ---------- UNUSUAL CONSUMPTION ----------

def detect_unusual_consumption(data, threshold=0.20):
    """
    Flag mileage that differs from a vehicle's average
    by more than the selected proportion.

    threshold=0.20 means a 20 percent difference.
    """
    if data is None or data.empty:
        return pd.DataFrame()

    if not {"vehicle_name", "mileage"}.issubset(data.columns):
        return pd.DataFrame()

    df = data.copy()
    df["mileage"] = pd.to_numeric(
        df["mileage"], errors="coerce"
    )
    df = df[
        df["mileage"].notna()
        & np.isfinite(df["mileage"])
        & (df["mileage"] > 0)
    ].copy()

    if df.empty:
        return df

    average = df.groupby("vehicle_name")["mileage"].transform("mean")

    df["average_vehicle_mileage"] = average
    df["percentage_difference"] = np.where(
        average > 0,
        (df["mileage"] - average).abs() / average,
        np.nan
    )

    unusual = df[
        df["percentage_difference"] > threshold
    ].copy()

    return unusual.reset_index(drop=True)


# ---------- INVALID READING REPORT ----------

def invalid_readings_report(data):
    """
    Return invalid records with a reason.
    Use raw, uncleaned data for this function.
    """
    if data is None or data.empty:
        return pd.DataFrame()

    df = data.copy()
    reasons = pd.Series("", index=df.index, dtype="object")

    checks = [
        ("fuel_litres", lambda s: s <= 0, "Fuel litres must be positive"),
        ("price_per_litre", lambda s: s <= 0, "Fuel price must be positive"),
        ("distance", lambda s: s <= 0, "Distance must be positive"),
        ("mileage", lambda s: s <= 0, "Mileage must be positive")
    ]

    for column, condition, message in checks:
        if column in df.columns:
            values = pd.to_numeric(df[column], errors="coerce")
            invalid = values.isna() | condition(values)
            reasons.loc[invalid] = reasons.loc[invalid].apply(
                lambda old: old + (("; " if old else "") + message)
            )

    if (
        "previous_odometer" in df.columns
        and "current_odometer" in df.columns
    ):
        previous = pd.to_numeric(
            df["previous_odometer"], errors="coerce"
        )
        current = pd.to_numeric(
            df["current_odometer"], errors="coerce"
        )
        invalid = (
            previous.isna() | current.isna()
            | (current <= previous)
        )
        reasons.loc[invalid] = reasons.loc[invalid].apply(
            lambda old: old + (
                ("; " if old else "")
                + "Current odometer must exceed previous reading"
            )
        )

    df["validation_reason"] = reasons
    return df[df["validation_reason"] != ""].reset_index(drop=True)


# ---------- CHART DATA ----------

def prepare_chart_data(data):
    """Prepare monthly and vehicle data for charts."""
    df = clean_fuel_data(data)

    if df.empty:
        return {
            "monthly_expenses": pd.DataFrame(),
            "monthly_fuel": pd.DataFrame(),
            "vehicle_mileage": pd.DataFrame(),
            "vehicle_fuel": pd.DataFrame()
        }

    df["fuel_date"] = pd.to_datetime(
        df["fuel_date"], errors="coerce"
    )
    df["month"] = df["fuel_date"].dt.to_period("M").astype(str)

    return {
        "monthly_expenses": df.groupby(
            "month", as_index=False
        )["total_cost"].sum(),

        "monthly_fuel": df.groupby(
            "month", as_index=False
        )["fuel_litres"].sum(),

        "vehicle_mileage": df.groupby(
            "vehicle_name", as_index=False
        )["mileage"].mean(),

        "vehicle_fuel": df.groupby(
            "vehicle_name", as_index=False
        )["fuel_litres"].sum()
    }
