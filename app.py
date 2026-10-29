import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error

from db_connection import get_connection

from analytics import (
    load_fuel_data,
    clean_fuel_data,
    vehicle_expense_report,
    monthly_expense_report,
    vehicle_comparison_report,
    period_comparison_report,
)

from calculations import (
    calculate_mileage,
    calculate_fuel_cost,
    calculate_total_fuel
)


app = Flask(__name__)
app.secret_key = "fuel-project-secret-key"

VEHICLE_TYPES = ["Car", "Bike", "Truck", "Bus", "Van", "Other"]
FUEL_TYPES = ["Petrol", "Diesel", "CNG", "Electric", "Other"]


# =========================================================
# DATABASE HELPERS
# =========================================================

def fetch_all(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def execute_sql(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(sql, params)
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


# =========================================================
# INVALID READING LOG
# =========================================================

def safe_decimal(value):
    """Convert a submitted value to Decimal, or return None."""
    try:
        if value is None or str(value).strip() == "":
            return None

        number = Decimal(str(value).strip())

        if not number.is_finite():
            return None

        return number

    except (InvalidOperation, ValueError, TypeError):
        return None


def safe_date(value):
    """Convert a submitted date to a date object, or return None."""
    try:
        return datetime.strptime(value or "", "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def log_invalid_reading(vehicle_id, reason):
    """
    Save a rejected fuel submission in invalid_readings.
    Invalid submissions are never inserted into fuel_entries.
    """
    form = request.form

    try:
        submitted_vehicle_id = vehicle_id

        if submitted_vehicle_id is None:
            try:
                submitted_vehicle_id = int(form.get("vehicle_id", ""))
            except (ValueError, TypeError):
                submitted_vehicle_id = None

        execute_sql(
            """
            INSERT INTO invalid_readings
                (vehicle_id, entered_date, previous_odometer,
                 current_odometer, fuel_litres, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                submitted_vehicle_id,
                safe_date(form.get("fuel_date")),
                safe_decimal(form.get("previous_odometer")),
                safe_decimal(form.get("current_odometer")),
                safe_decimal(form.get("fuel_litres")),
                str(reason)[:255]
            )
        )

    except Exception:
        # Keep the original validation error visible even if logging fails.
        app.logger.exception("Could not save invalid-reading log")


# =========================================================
# INPUT VALIDATION
# =========================================================

def validate_vehicle_name(value):
    value = (value or "").strip()

    if len(value) < 2:
        return False, "Vehicle name must contain at least 2 characters."

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ._-]*", value):
        return False, (
            "Vehicle name must start with a letter and contain "
            "only valid characters."
        )

    return True, value


def validate_vehicle_number(value):
    value = re.sub(r"\s+", "", (value or "").upper())

    pattern = r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}"

    if not re.fullmatch(pattern, value):
        return False, "Enter a valid registration number, e.g. AP03AB1234."

    return True, value


def validate_positive_number(value, field_name, allow_zero=False):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return False, f"{field_name} must be a valid number."

    if not number.is_finite():
        return False, f"{field_name} must be finite."

    if number < 0:
        return False, f"{field_name} cannot be negative."

    if number == 0 and not allow_zero:
        return False, f"{field_name} must be greater than zero."

    return True, number


def validate_fuel_date(value):
    try:
        parsed_date = datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return False, "Enter a valid fuel date."

    if parsed_date > date.today():
        return False, "Fuel date cannot be in the future."

    return True, parsed_date


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def dashboard():
    try:
        summary = fetch_one("""
            SELECT
                (SELECT COUNT(*) FROM vehicles) AS total_vehicles,
                (SELECT COUNT(*) FROM fuel_entries) AS total_entries,
                (SELECT COALESCE(SUM(fuel_litres), 0)
                 FROM fuel_entries) AS total_fuel,
                (SELECT COALESCE(SUM(total_cost), 0)
                 FROM fuel_entries) AS total_cost,
                (SELECT COALESCE(AVG(mileage), 0)
                 FROM fuel_entries
                 WHERE mileage > 0) AS avg_mileage
        """)

        recent_entries = fetch_all("""
            SELECT f.entry_id, v.vehicle_name, v.vehicle_number,
                   f.fuel_date, f.distance, f.fuel_litres,
                   f.mileage, f.total_cost
            FROM fuel_entries f
            JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            ORDER BY f.fuel_date DESC, f.entry_id DESC
            LIMIT 10
        """)

        chart_images = [
            "mileage_comparison.png",
            "monthly_expenses.png",
            "fuel_consumption.png",
            "cost_per_kilometre.png",
            "monthly_consumption.png",
            "vehicle_performance.png"
        ]

        try:
            import visualizations

            if hasattr(visualizations, "generate_all_charts"):
                visualizations.generate_all_charts()
        except Exception:
            app.logger.exception("Chart generation failed")

        summary = summary or {}

        return render_template(
            "dashboard.html",
            summary=summary,
            total_vehicles=summary.get("total_vehicles", 0),
            total_entries=summary.get("total_entries", 0),
            total_fuel=summary.get("total_fuel", 0),
            total_cost=summary.get("total_cost", 0),
            avg_mileage=summary.get("avg_mileage", 0),
            recent_entries=recent_entries,
            chart_images=chart_images
        )

    except Error:
        app.logger.exception("Dashboard database error")
        flash("Unable to load dashboard. Check your database connection.", "error")

        return render_template(
            "dashboard.html",
            summary={},
            total_vehicles=0,
            total_entries=0,
            total_fuel=0,
            total_cost=0,
            avg_mileage=0,
            recent_entries=[],
            chart_images=[]
        )


# =========================================================
# VEHICLE MANAGEMENT
# =========================================================

@app.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    if request.method == "POST":
        valid, vehicle_name = validate_vehicle_name(
            request.form.get("vehicle_name")
        )

        if not valid:
            flash(vehicle_name, "error")
            return redirect(url_for("vehicles"))

        valid, vehicle_number = validate_vehicle_number(
            request.form.get("vehicle_number")
        )

        if not valid:
            flash(vehicle_number, "error")
            return redirect(url_for("vehicles"))

        vehicle_type = request.form.get("vehicle_type", "").strip()
        fuel_type = request.form.get("fuel_type", "").strip()

        if vehicle_type not in VEHICLE_TYPES:
            flash("Select a valid vehicle type.", "error")
            return redirect(url_for("vehicles"))

        if fuel_type not in FUEL_TYPES:
            flash("Select a valid fuel type.", "error")
            return redirect(url_for("vehicles"))

        try:
            execute_sql("""
                INSERT INTO vehicles
                    (vehicle_name, vehicle_number,
                     vehicle_type, fuel_type)
                VALUES (%s, %s, %s, %s)
            """, (
                vehicle_name,
                vehicle_number,
                vehicle_type,
                fuel_type
            ))

            flash("Vehicle added successfully!", "success")

        except Error as error:
            if getattr(error, "errno", None) == 1062:
                flash("This registration number already exists.", "error")
            else:
                app.logger.exception("Vehicle insertion failed")
                flash("Could not save the vehicle. Check the database.", "error")

        return redirect(url_for("vehicles"))

    try:
        vehicle_list = fetch_all("""
            SELECT vehicle_id, vehicle_name, vehicle_number,
                   vehicle_type, fuel_type, created_at
            FROM vehicles
            ORDER BY vehicle_id DESC
        """)
    except Error:
        app.logger.exception("Could not load vehicles")
        vehicle_list = []
        flash("Could not load vehicle records.", "error")

    return render_template(
        "vehicles.html",
        vehicles=vehicle_list,
        vehicle_types=VEHICLE_TYPES,
        fuel_types=FUEL_TYPES
    )


# =========================================================
# FUEL ENTRY MANAGEMENT
# =========================================================

@app.route("/fuel-entries", methods=["GET", "POST"])
def fuel_entries():

    if request.method == "POST":

        # Get form values
        vehicle_id = request.form.get("vehicle_id", "").strip()
        fuel_date = request.form.get("fuel_date", "").strip()
        previous_odometer = request.form.get("previous_odometer", "").strip()
        current_odometer = request.form.get("current_odometer", "").strip()
        fuel_litres = request.form.get("fuel_litres", "").strip()
        price_per_litre = request.form.get("price_per_litre", "").strip()

        # Validate vehicle ID
        if not vehicle_id.isdigit():
            flash("Please select a valid vehicle.", "error")
            return redirect(url_for("fuel_entries"))

        vehicle_id = int(vehicle_id)

        # Validate date
        if not validate_fuel_date(fuel_date):
            flash("Please enter a valid fuel date.", "error")
            log_invalid_reading(vehicle_id, "Invalid fuel date")
            return redirect(url_for("fuel_entries"))

        # Validate odometer readings
        previous = validate_positive_number(
            previous_odometer, "Previous odometer", allow_zero=True
        )

        current = validate_positive_number(
            current_odometer, "Current odometer", allow_zero=True
        )

        if previous is None or current is None:
            flash("Please enter valid odometer readings.", "error")
            log_invalid_reading(vehicle_id, "Invalid odometer reading")
            return redirect(url_for("fuel_entries"))

        if current <= previous:
            flash(
                "Current odometer must be greater than previous odometer.",
                "error"
            )
            log_invalid_reading(
                vehicle_id, "Current odometer must exceed previous odometer"
            )
            return redirect(url_for("fuel_entries"))

        # Check the latest saved fuel entry
        latest_entry = fetch_one(
            """
            SELECT current_odometer, fuel_date
            FROM fuel_entries
            WHERE vehicle_id = %s
            ORDER BY fuel_date DESC, entry_id DESC
            LIMIT 1
            """,
            (vehicle_id,)
        )

        if latest_entry:
            latest_odometer = float(latest_entry["current_odometer"])
            latest_date = latest_entry["fuel_date"]

            if float(previous) != latest_odometer:
                flash(
                    "Previous odometer must match the latest saved "
                    "odometer reading for this vehicle.",
                    "error"
                )
                log_invalid_reading(
                    vehicle_id, "Previous odometer does not match latest reading"
                )
                return redirect(url_for("fuel_entries"))

            if isinstance(latest_date, datetime):
                latest_date = latest_date.date()

            submitted_date = date.fromisoformat(fuel_date)

            if submitted_date < latest_date:
                flash(
                    "Fuel date cannot be earlier than the latest saved entry.",
                    "error"
                )
                log_invalid_reading(
                    vehicle_id, "Fuel date is earlier than latest saved entry"
                )
                return redirect(url_for("fuel_entries"))

        # Validate fuel quantity and price
        litres = validate_positive_number(
            fuel_litres, "Fuel litres"
        )

        price = validate_positive_number(
            price_per_litre, "Price per litre"
        )

        if litres is None or price is None:
            flash(
                "Fuel litres and price must be greater than zero.",
                "error"
            )
            log_invalid_reading(
                vehicle_id, "Invalid fuel quantity or price"
            )
            return redirect(url_for("fuel_entries"))

        # Calculate values using calculations.py
        distance = float(current) - float(previous)

        try:
            mileage = calculate_mileage(
                float(distance), float(litres)
            )

            total_cost = calculate_fuel_cost(
                float(litres), float(price)
            )

        except ValueError as error:
            flash(str(error), "error")
            log_invalid_reading(vehicle_id, str(error))
            return redirect(url_for("fuel_entries"))

        # Save the fuel entry
        query = """
            INSERT INTO fuel_entries
            (
                vehicle_id,
                fuel_date,
                previous_odometer,
                current_odometer,
                fuel_litres,
                price_per_litre,
                distance,
                mileage,
                total_cost
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            vehicle_id,
            fuel_date,
            float(previous),
            float(current),
            float(litres),
            float(price),
            float(distance),
            float(mileage),
            float(total_cost)
        )

        try:
            execute_sql(query, values)
            flash("Fuel entry added successfully!", "success")

        except Error as error:
            flash("Could not save fuel entry. Please check the database.", "error")
            print("Database error:", error)

        return redirect(url_for("fuel_entries"))

    # GET: Display vehicles and existing fuel entries
    vehicles = fetch_all(
        """
        SELECT vehicle_id, vehicle_name, vehicle_number
        FROM vehicles
        ORDER BY vehicle_id DESC
        """
    )

    entries = fetch_all(
        """
        SELECT
            f.entry_id,
            f.vehicle_id,
            v.vehicle_name,
            v.vehicle_number,
            f.fuel_date,
            f.previous_odometer,
            f.current_odometer,
            f.fuel_litres,
            f.price_per_litre,
            f.distance,
            f.mileage,
            f.total_cost
        FROM fuel_entries f
        JOIN vehicles v ON f.vehicle_id = v.vehicle_id
        ORDER BY f.fuel_date DESC, f.entry_id DESC
        """
    )

    return render_template(
        "fuel_entries.html",
        vehicles=vehicles,
        entries=entries
    )

# =========================================================
# REPORTS - FOUR REPORTS ONLY
# =========================================================


@app.route("/reports")
def reports():
    try:
        # Load fuel records from MySQL
        raw_data = load_fuel_data()

        # Clean data for analysis
        clean_data = clean_fuel_data(raw_data)

        # 1. Vehicle Expense Report
        vehicle_expenses = vehicle_expense_report(clean_data)

        # Add vehicle number and entry count
        if not vehicle_expenses.empty:
            vehicle_details = raw_data[
                ["vehicle_name", "vehicle_number", "entry_id"]
            ].copy()

            vehicle_details = vehicle_details.groupby(
                "vehicle_name", as_index=False
            ).agg(
                vehicle_number=("vehicle_number", "first"),
                entry_count=("entry_id", "count")
            )

            vehicle_expenses = vehicle_expenses.merge(
                vehicle_details, on="vehicle_name", how="left"
            )

        # 2. Monthly Expense Report
        monthly_expenses = monthly_expense_report(clean_data)

        # Add the fields expected by reports.html
        if not monthly_expenses.empty:
            monthly_details = clean_data.copy()
            monthly_details["period"] = (
                monthly_details["fuel_date"]
                .dt.to_period("M")
                .astype(str)
            )

            counts = monthly_details.groupby(
                "period", as_index=False
            ).agg(
                total_entries=("entry_id", "count"),
                total_fuel=("fuel_litres", "sum"),
                total_distance=("distance", "sum")
            )

            monthly_expenses = monthly_expenses.rename(
                columns={"month": "period"}
            ).merge(counts, on="period", how="left")

            monthly_expenses = monthly_expenses.sort_values(
                "period", ascending=False
            )

        # 3. Vehicle Comparison Report
        vehicle_comparison = vehicle_comparison_report(clean_data)

        if not vehicle_comparison.empty:
            vehicle_details = raw_data[
                ["vehicle_name", "vehicle_number"]
            ].drop_duplicates(subset=["vehicle_name"])

            vehicle_comparison = vehicle_comparison.merge(
                vehicle_details, on="vehicle_name", how="left"
            )

            vehicle_comparison = vehicle_comparison.rename(
                columns={"average_mileage": "avg_mileage"}
            )

        # 4. Period Comparison Report
        period_comparison = period_comparison_report(clean_data)

        if not period_comparison.empty:
            monthly_details = clean_data.copy()
            monthly_details["period"] = (
                monthly_details["fuel_date"]
                .dt.to_period("M")
                .astype(str)
            )

            counts = monthly_details.groupby(
                "period", as_index=False
            ).agg(
                total_entries=("entry_id", "count"),
                total_fuel=("fuel_litres", "sum"),
                total_distance=("distance", "sum")
            )

            period_comparison = period_comparison.rename(
                columns={"month": "period"}
            ).merge(counts, on="period", how="left")

        return render_template(
            "reports.html",
            vehicle_expenses=vehicle_expenses.to_dict("records"),
            monthly_expenses=monthly_expenses.to_dict("records"),
            vehicle_comparison=vehicle_comparison.to_dict("records"),
            period_comparison=period_comparison.to_dict("records")
        )

    except Exception:
        app.logger.exception("Reports could not be loaded")

        return render_template(
            "reports.html",
            vehicle_expenses=[],
            monthly_expenses=[],
            vehicle_comparison=[],
            period_comparison=[]
        )

# =========================================================
# INVALID READINGS LOG
# =========================================================

@app.route("/invalid-readings")
def invalid_readings():
    try:
        invalid_records = fetch_all("""
            SELECT
                l.log_id,
                v.vehicle_name,
                v.vehicle_number,
                l.entered_date,
                l.previous_odometer,
                l.current_odometer,
                l.fuel_litres,
                l.reason,
                l.logged_at
            FROM invalid_readings l
            LEFT JOIN vehicles v
                ON l.vehicle_id = v.vehicle_id
            ORDER BY l.logged_at DESC, l.log_id DESC
        """)

    except Error:
        app.logger.exception("Could not load invalid-reading log")
        invalid_records = []
        flash("Could not load invalid readings. Check the database.", "error")

    return render_template(
        "invalid_readings.html",
        invalid_readings=invalid_records,
        records=invalid_records
    )


# =========================================================
# API ROUTES
# =========================================================

@app.route("/api/vehicles", methods=["GET"])
def api_vehicles():
    try:
        return {
            "success": True,
            "data": fetch_all("""
                SELECT vehicle_id, vehicle_name, vehicle_number,
                       vehicle_type, fuel_type
                FROM vehicles
                ORDER BY vehicle_id
            """)
        }
    except Error:
        app.logger.exception("Vehicle API failed")
        return {"success": False, "error": "Database error"}, 500


@app.route("/api/vehicles/<int:vehicle_id>", methods=["GET"])
def api_vehicle_detail(vehicle_id):
    try:
        vehicle = fetch_one("""
            SELECT vehicle_id, vehicle_name, vehicle_number,
                   vehicle_type, fuel_type
            FROM vehicles
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}, 404

        return {"success": True, "data": vehicle}

    except Error:
        app.logger.exception("Vehicle detail API failed")
        return {"success": False, "error": "Database error"}, 500


@app.route("/api/fuel-entries", methods=["GET"])
def api_fuel_entries():
    try:
        entries = fetch_all("""
            SELECT f.entry_id, f.vehicle_id,
                   v.vehicle_name, v.vehicle_number,
                   f.fuel_date, f.previous_odometer,
                   f.current_odometer, f.distance,
                   f.fuel_litres, f.price_per_litre,
                   f.mileage, f.total_cost
            FROM fuel_entries f
            JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            ORDER BY f.entry_id DESC
        """)

        return {"success": True, "data": entries}

    except Error:
        app.logger.exception("Fuel entries API failed")
        return {"success": False, "error": "Database error"}, 500


@app.route("/api/fuel-entries/<int:entry_id>", methods=["GET"])
def api_fuel_entry_detail(entry_id):
    try:
        entry = fetch_one("""
            SELECT f.entry_id, f.vehicle_id,
                   v.vehicle_name, v.vehicle_number,
                   f.fuel_date, f.previous_odometer,
                   f.current_odometer, f.distance,
                   f.fuel_litres, f.price_per_litre,
                   f.mileage, f.total_cost
            FROM fuel_entries f
            JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            WHERE f.entry_id = %s
        """, (entry_id,))

        if not entry:
            return {"success": False, "error": "Fuel entry not found"}, 404

        return {"success": True, "data": entry}

    except Error:
        app.logger.exception("Fuel entry detail API failed")
        return {"success": False, "error": "Database error"}, 500


@app.route("/api/vehicles/<int:vehicle_id>/fuel-entries", methods=["GET"])
def api_vehicle_fuel_entries(vehicle_id):
    try:
        vehicle = fetch_one(
            "SELECT vehicle_id FROM vehicles WHERE vehicle_id = %s",
            (vehicle_id,)
        )

        if not vehicle:
            return {"success": False, "error": "Vehicle not found"}, 404

        entries = fetch_all("""
            SELECT entry_id, vehicle_id, fuel_date,
                   previous_odometer, current_odometer,
                   distance, fuel_litres, price_per_litre,
                   mileage, total_cost
            FROM fuel_entries
            WHERE vehicle_id = %s
            ORDER BY fuel_date DESC
        """, (vehicle_id,))

        return {"success": True, "data": entries}

    except Error:
        app.logger.exception("Vehicle fuel history API failed")
        return {"success": False, "error": "Database error"}, 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)