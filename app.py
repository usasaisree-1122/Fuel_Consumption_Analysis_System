import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import BytesIO

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error

from db_connection import get_connection
from calculations import calculate_mileage, calculate_fuel_cost
from analytics import (load_fuel_data, clean_fuel_data, vehicle_expense_report,
                      monthly_expense_report, vehicle_comparison_report,
                      period_comparison_report)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret-key")

VEHICLE_TYPES = ["Car", "Bike", "Truck", "Bus", "Van", "Scooter", "Other"]
FUEL_TYPES = ["Petrol", "Diesel", "CNG", "Electric", "Other"]


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


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You do not have permission to perform this action.", "error")
                return redirect(url_for("dashboard"))
            return function(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    return fetch_one("SELECT user_id, full_name, email, role FROM users WHERE user_id=%s",
                     (session["user_id"],))


def visible_vehicle_condition():
    role = session.get("role")
    user_id = session.get("user_id")
    if role == "fleet_manager":
        return "", ()
    if role == "individual_owner":
        return " WHERE v.owner_id=%s", (user_id,)
    if role == "staff":
        return (
            " JOIN staff_assignments sa ON sa.vehicle_id=v.vehicle_id "
            " WHERE sa.staff_user_id=%s",
            (user_id,)
        )
    return " WHERE 1=0", ()


def get_visible_vehicles():
    extra, params = visible_vehicle_condition()
    return fetch_all(
        "SELECT v.vehicle_id, v.vehicle_name, v.vehicle_number, v.vehicle_type, "
        "v.fuel_type, v.created_at FROM vehicles v" + extra +
        " ORDER BY v.vehicle_id DESC", params)



def can_access_vehicle(vehicle_id):
    role = session.get("role")
    user_id = session.get("user_id")

    if role == "fleet_manager":
        return fetch_one(
            "SELECT vehicle_id FROM vehicles WHERE vehicle_id=%s",
            (vehicle_id,)
        ) is not None

    if role == "individual_owner":
        return fetch_one(
            "SELECT vehicle_id FROM vehicles WHERE vehicle_id=%s AND owner_id=%s",
            (vehicle_id, user_id)
        ) is not None

    if role == "staff":
        return fetch_one("""
            SELECT vehicle_id FROM staff_assignments
            WHERE vehicle_id=%s AND staff_user_id=%s
        """, (vehicle_id, user_id)) is not None

    return False


def log_invalid_reading(vehicle_id, reason):
    form = request.form
    def number(name):
        try:
            return Decimal(form.get(name, "").strip())
        except (InvalidOperation, ValueError, TypeError):
            return None
    try:
        execute_sql(
            """INSERT INTO invalid_readings
               (vehicle_id, entered_date, previous_odometer, current_odometer,
                fuel_litres, reason) VALUES (%s,%s,%s,%s,%s,%s)""",
            (vehicle_id, form.get("fuel_date") or None, number("previous_odometer"),
             number("current_odometer"), number("fuel_litres"), str(reason)[:255]))
    except Exception:
        app.logger.exception("Could not save invalid reading")


def positive_decimal(value, label, allow_zero=False):
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(label + " must be a valid number.")
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(label + " must be " + ("zero or positive." if allow_zero else "greater than zero."))
    return number


@app.context_processor
def inject_user():
    return {"logged_user": session.get("name"), "logged_role": session.get("role")}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "individual_owner")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email and a password of at least 6 characters.", "error")
            return redirect(url_for("register"))
        if role not in ("individual_owner", "fleet_manager"):
            flash("Invalid account type.", "error")
            return redirect(url_for("register"))
        try:
            execute_sql(
                "INSERT INTO users (full_name,email,password_hash,role) VALUES (%s,%s,%s,%s)",
                (name, email, generate_password_hash(password), role))
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except Error as error:
            if getattr(error, "errno", None) == 1062:
                flash("This email is already registered.", "error")
            else:
                app.logger.exception("Registration failed")
                flash("Could not create account.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE email=%s", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["name"] = user["full_name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/")
@login_required
def dashboard():

    # Get vehicles accessible to the logged-in user
    vehicles = get_visible_vehicles()
    vehicle_ids = [v["vehicle_id"] for v in vehicles]

    vehicle_count = len(vehicle_ids)

    if vehicle_ids:

        marks = ",".join(["%s"] * len(vehicle_ids))
        params = tuple(vehicle_ids)

        # Total fuel entries
        entry_count = fetch_one(
            f"SELECT COUNT(*) AS n FROM fuel_entries "
            f"WHERE vehicle_id IN ({marks})",
            params
        )["n"]

        # Total fuel consumed
        total_fuel = fetch_one(
            f"SELECT COALESCE(SUM(fuel_litres), 0) AS n "
            f"FROM fuel_entries WHERE vehicle_id IN ({marks})",
            params
        )["n"]

        # Total fuel expenditure
        total_cost = fetch_one(
            f"SELECT COALESCE(SUM(total_cost), 0) AS n "
            f"FROM fuel_entries WHERE vehicle_id IN ({marks})",
            params
        )["n"]

        # Average mileage
        average = fetch_one(
            f"SELECT COALESCE(AVG(mileage), 0) AS n "
            f"FROM fuel_entries "
            f"WHERE vehicle_id IN ({marks}) AND mileage > 0",
            params
        )["n"]

        # Recent fuel entries
        recent = fetch_all(
            f"""
            SELECT f.*, v.vehicle_name, v.vehicle_number
            FROM fuel_entries f
            JOIN vehicles v ON v.vehicle_id = f.vehicle_id
            WHERE f.vehicle_id IN ({marks})
            ORDER BY f.fuel_date DESC, f.entry_id DESC
            LIMIT 10
            """,
            params
        )

    else:
        entry_count = 0
        total_fuel = 0
        total_cost = 0
        average = 0
        recent = []

    # Generate role-specific charts
    from visualizations import generate_all_charts

    chart_key = f"user_{session['user_id']}"

    chart_images = generate_all_charts(
        vehicle_ids=vehicle_ids,
        chart_key=chart_key
    )

    return render_template(
        "dashboard.html",
        total_vehicles=vehicle_count,
        total_entries=entry_count,
        total_fuel=total_fuel,
        total_cost=total_cost,
        avg_mileage=average,
        recent_entries=recent,
        chart_images=chart_images
    )


@app.route("/vehicles", methods=["GET", "POST"])
@login_required
def vehicles():
    if request.method == "POST":
        if session["role"] == "staff":
            flash("Staff cannot add vehicles.", "error")
            return redirect(url_for("vehicles"))
        name = request.form.get("vehicle_name", "").strip()
        number = re.sub(r"\s+", "", request.form.get("vehicle_number", "").upper())
        vehicle_type = request.form.get("vehicle_type", "")
        fuel_type = request.form.get("fuel_type", "")
        if len(name) < 2 or not re.fullmatch(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}", number):
            flash("Enter a valid vehicle name and registration number.", "error")
            return redirect(url_for("vehicles"))
        if vehicle_type not in VEHICLE_TYPES or fuel_type not in FUEL_TYPES:
            flash("Select valid vehicle and fuel types.", "error")
            return redirect(url_for("vehicles"))
        try:
            owner_id = session["user_id"] if session["role"] == "individual_owner" else None
            execute_sql("""INSERT INTO vehicles
                (vehicle_name,vehicle_number,vehicle_type,fuel_type,owner_id)
                VALUES (%s,%s,%s,%s,%s)""",
                (name, number, vehicle_type, fuel_type, owner_id))
            flash("Vehicle added successfully.", "success")
        except Error:
            app.logger.exception("Vehicle insert failed")
            flash("Could not add vehicle. Registration number may already exist.", "error")
        return redirect(url_for("vehicles"))
    return render_template("vehicles.html", vehicles=get_visible_vehicles(),
                           vehicle_types=VEHICLE_TYPES, fuel_types=FUEL_TYPES)


@app.route("/vehicles/<int:vehicle_id>", methods=["PUT", "DELETE"])
@login_required
def vehicle_api_detail(vehicle_id):
    if session["role"] == "staff" or not can_access_vehicle(vehicle_id):
        return jsonify({"success": False, "error": "Not permitted"}), 403
    if request.method == "DELETE":
        execute_sql("DELETE FROM vehicles WHERE vehicle_id=%s", (vehicle_id,))
        return jsonify({"success": True, "message": "Vehicle deleted"})
    data = request.get_json(silent=True) or {}
    fields = ["vehicle_name", "vehicle_number", "vehicle_type", "fuel_type"]
    updates, values = [], []
    for field in fields:
        if field in data:
            updates.append(field + "=%s")
            values.append(data[field])
    if not updates:
        return jsonify({"success": False, "error": "No fields supplied"}), 400
    values.append(vehicle_id)
    execute_sql("UPDATE vehicles SET " + ",".join(updates) + " WHERE vehicle_id=%s", tuple(values))
    return jsonify({"success": True, "message": "Vehicle updated"})


@app.route("/fuel-entries", methods=["GET", "POST"])
@login_required
def fuel_entries():
    visible = get_visible_vehicles()
    if request.method == "POST":
        try:
            vehicle_id = int(request.form.get("vehicle_id", "0"))
            if not can_access_vehicle(vehicle_id):
                raise ValueError("You cannot add an entry for this vehicle.")
            fuel_date = datetime.strptime(request.form.get("fuel_date", ""), "%Y-%m-%d").date()
            if fuel_date > date.today():
                raise ValueError("Fuel date cannot be in the future.")
            previous = positive_decimal(request.form.get("previous_odometer"), "Previous odometer", True)
            current = positive_decimal(request.form.get("current_odometer"), "Current odometer", True)
            litres = positive_decimal(request.form.get("fuel_litres"), "Fuel quantity")
            price = positive_decimal(request.form.get("price_per_litre"), "Price per litre")
            if current <= previous:
                raise ValueError("Current odometer must be greater than previous odometer.")
            latest = fetch_one("""SELECT current_odometer,fuel_date FROM fuel_entries
                                  WHERE vehicle_id=%s ORDER BY fuel_date DESC,entry_id DESC LIMIT 1""",
                               (vehicle_id,))
            if latest and previous != Decimal(str(latest["current_odometer"])):
                raise ValueError("Previous odometer must match the latest saved reading.")
            if latest and fuel_date < latest["fuel_date"]:
                raise ValueError("Fuel date cannot be earlier than the latest entry.")
            distance = current - previous
            mileage = calculate_mileage(float(distance), float(litres))
            cost = calculate_fuel_cost(float(litres), float(price))
            full_tank = 1 if request.form.get("full_tank_flag") == "on" else 0
            execute_sql("""INSERT INTO fuel_entries
                (vehicle_id, fuel_date, previous_odometer, current_odometer,
                 fuel_litres, price_per_litre, distance, mileage, total_cost,
                 full_tank_flag, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (vehicle_id, fuel_date, previous, current, litres, price,
                         distance, mileage, cost, full_tank, session["user_id"]))
            flash("Fuel entry added successfully.", "success")
        except (ValueError, InvalidOperation) as error:
            flash(str(error), "error")
            try:
                log_invalid_reading(locals().get("vehicle_id"), str(error))
            except Exception:
                pass
        except Error:
            app.logger.exception("Fuel entry insert failed")
            flash("Could not save fuel entry.", "error")
        return redirect(url_for("fuel_entries"))
    ids = [v["vehicle_id"] for v in visible]
    entries = []
    if ids:
        marks = ",".join(["%s"] * len(ids))
        entries = fetch_all("""SELECT f.*,v.vehicle_name,v.vehicle_number
            FROM fuel_entries f JOIN vehicles v ON v.vehicle_id=f.vehicle_id
            WHERE f.vehicle_id IN (""" + marks + """)
            ORDER BY f.fuel_date DESC,f.entry_id DESC""", tuple(ids))
    return render_template("fuel_entries.html", vehicles=visible, entries=entries,
                           now_date=date.today().isoformat())


@app.route("/api/fuel-entries", methods=["GET", "POST"])
@login_required
def fuel_entries_api():
    if request.method == "GET":
        ids = [v["vehicle_id"] for v in get_visible_vehicles()]
        if not ids:
            return jsonify({"success": True, "data": []})
        marks = ",".join(["%s"] * len(ids))
        rows = fetch_all("SELECT * FROM fuel_entries WHERE vehicle_id IN (" + marks + ") ORDER BY entry_id DESC", tuple(ids))
        return jsonify({"success": True, "data": rows})
    data = request.get_json(silent=True) or {}
    required = ["vehicle_id", "fuel_date", "previous_odometer", "current_odometer", "fuel_litres", "price_per_litre"]
    if any(k not in data for k in required):
        return jsonify({"success": False, "error": "Missing fields"}), 400
    try:
        vehicle_id = int(data["vehicle_id"])
        if not can_access_vehicle(vehicle_id):
            return jsonify({"success": False, "error": "Not permitted"}), 403
        previous = positive_decimal(data["previous_odometer"], "Previous odometer", True)
        current = positive_decimal(data["current_odometer"], "Current odometer", True)
        litres = positive_decimal(data["fuel_litres"], "Fuel litres")
        price = positive_decimal(data["price_per_litre"], "Price per litre")
        if current <= previous:
            raise ValueError("Current odometer must be greater than previous odometer.")
        fuel_date = datetime.strptime(data["fuel_date"], "%Y-%m-%d").date()
        distance = current - previous
        mileage = calculate_mileage(float(distance), float(litres))
        cost = calculate_fuel_cost(float(litres), float(price))
        entry_id = execute_sql("""INSERT INTO fuel_entries
    (vehicle_id, fuel_date, previous_odometer, current_odometer,
     fuel_litres, price_per_litre, distance, mileage, total_cost,
     full_tank_flag, created_by)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
    (vehicle_id, fuel_date, previous, current, litres, price,
     distance, mileage, cost,
     1 if data.get("full_tank_flag") else 0,
     session["user_id"]))
        return jsonify({"success": True, "entry_id": entry_id}), 201
    except (ValueError, InvalidOperation) as error:
        return jsonify({"success": False, "error": str(error)}), 400



@app.route("/api/fuel-entries/<int:entry_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def fuel_entry_detail_api(entry_id):
    entry = fetch_one(
        "SELECT * FROM fuel_entries WHERE entry_id=%s",
        (entry_id,)
    )
    if not entry:
        return jsonify({"success": False, "error": "Entry not found"}), 404

    if not can_access_vehicle(entry["vehicle_id"]):
        return jsonify({"success": False, "error": "Not permitted"}), 403

    role = session["role"]
    user_id = session["user_id"]

    if request.method == "GET":
        return jsonify({"success": True, "data": entry})

    # Staff can edit/delete only entries they created
    if role == "staff" and entry["created_by"] != user_id:
        return jsonify({
            "success": False,
            "error": "You can only modify entries created by you."
        }), 403

    if request.method == "DELETE":
        execute_sql(
            "DELETE FROM fuel_entries WHERE entry_id=%s",
            (entry_id,)
        )
        return jsonify({"success": True, "message": "Entry deleted"})

    data = request.get_json(silent=True) or {}

    allowed = [
        "fuel_date",
        "previous_odometer",
        "current_odometer",
        "fuel_litres",
        "price_per_litre"
    ]

    updates = []
    values = []

    for key in allowed:
        if key in data:
            updates.append(key + "=%s")
            values.append(data[key])

    if not updates:
        return jsonify({"success": False, "error": "No fields supplied"}), 400

    # Recalculate derived values
    try:
        updated = dict(entry)
        updated.update(data)

        if "fuel_date" in data:
            updated["fuel_date"] = datetime.strptime(
                data["fuel_date"][:10], "%Y-%m-%d"
            ).date()

        previous = positive_decimal(
            updated["previous_odometer"], "Previous odometer", True
        )
        current = positive_decimal(
            updated["current_odometer"], "Current odometer", True
        )
        litres = positive_decimal(updated["fuel_litres"], "Fuel litres")
        price = positive_decimal(updated["price_per_litre"], "Price per litre")

        if current <= previous:
            raise ValueError("Current odometer must be greater than previous odometer.")

        if updated["fuel_date"] > date.today():
            raise ValueError("Fuel date cannot be in the future.")
        full_tank = 1 if data.get("full_tank_flag", entry["full_tank_flag"]) else 0
        distance = current - previous
        mileage = calculate_mileage(float(distance), float(litres))
        cost = calculate_fuel_cost(float(litres), float(price))

        execute_sql("""
            UPDATE fuel_entries
            SET fuel_date=%s, previous_odometer=%s, current_odometer=%s,
                fuel_litres=%s, price_per_litre=%s,
                distance=%s, mileage=%s, total_cost=%s, full_tank_flag=%s
            WHERE entry_id=%s
        """, (
            updated["fuel_date"], previous, current, litres, price,
            distance, mileage, cost, full_tank, entry_id
        ))

        return jsonify({"success": True, "message": "Entry updated successfully"})

    except (ValueError, InvalidOperation) as error:
        return jsonify({"success": False, "error": str(error)}), 400

    except Error:
        app.logger.exception("Fuel entry update failed")
        return jsonify({"success": False, "error": "Could not update entry"}), 500


@app.route("/reports")
@login_required
def reports():
    raw = load_fuel_data()
    ids = [v["vehicle_id"] for v in get_visible_vehicles()]
    if session["role"] != "fleet_manager":
        raw = raw[raw["vehicle_id"].isin(ids)] if not raw.empty else raw
    clean = clean_fuel_data(raw)
    vehicle = vehicle_expense_report(clean)
    monthly = monthly_expense_report(clean)
    comparison = vehicle_comparison_report(clean)
    period = period_comparison_report(clean)
    return render_template("reports.html",
        vehicle_expenses=vehicle.to_dict("records"),
        monthly_expenses=monthly.to_dict("records"),
        vehicle_comparison=comparison.to_dict("records"),
        period_comparison=period.to_dict("records"))


@app.route("/reports/export/<kind>")
@login_required
def export_report(kind):
    raw = load_fuel_data()
    ids = [v["vehicle_id"] for v in get_visible_vehicles()]
    if session["role"] != "fleet_manager":
        raw = raw[raw["vehicle_id"].isin(ids)] if not raw.empty else raw
    clean = clean_fuel_data(raw)
    if kind == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            clean.to_excel(writer, index=False, sheet_name="Fuel Records")
            vehicle_expense_report(clean).to_excel(writer, index=False, sheet_name="Vehicle Expenses")
            monthly_expense_report(clean).to_excel(writer, index=False, sheet_name="Monthly Expenses")
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="fuel_report.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if kind == "pdf":
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        rows = [["Vehicle", "Date", "Distance", "Litres", "Mileage", "Cost"]]
        for _, row in clean.iterrows():
            rows.append([str(row.get("vehicle_name","")), str(row.get("fuel_date","")),
                         str(round(float(row.get("distance",0)),2)),
                         str(round(float(row.get("fuel_litres",0)),2)),
                         str(round(float(row.get("mileage",0)),2)),
                         str(round(float(row.get("total_cost",0)),2))])
        table = Table(rows, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#173b68")),
                                   ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                   ("GRID",(0,0),(-1,-1),0.5,colors.grey),
                                   ("FONTSIZE",(0,0),(-1,-1),8)]))
        doc.build([Paragraph("Fuel Consumption Report", styles["Title"]), Spacer(1,12), table])
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="fuel_report.pdf",
                         mimetype="application/pdf")
    return "Unknown export format", 404


@app.route("/invalid-readings")
@login_required
@roles_required("fleet_manager")
def invalid_readings():
    records = fetch_all("""SELECT l.*,v.vehicle_name,v.vehicle_number
        FROM invalid_readings l LEFT JOIN vehicles v ON v.vehicle_id=l.vehicle_id
        ORDER BY l.logged_at DESC,l.log_id DESC""")
    return render_template("invalid_readings.html", records=records)


@app.route("/staff", methods=["GET", "POST"])
@login_required
@roles_required("fleet_manager")
def staff():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        vehicle_ids = request.form.getlist("vehicle_ids")
        if not name or not email or len(password) < 6:
            flash("Enter staff details and a password of at least 6 characters.", "error")
        else:
            try:
                staff_id = execute_sql("INSERT INTO users(full_name,email,password_hash,role) VALUES(%s,%s,%s,'staff')",
                    (name, email, generate_password_hash(password)))
                for vehicle_id in vehicle_ids:
                    execute_sql(
                        """INSERT IGNORE INTO staff_assignments
                           (vehicle_id, staff_user_id, assigned_by)
                           VALUES (%s, %s, %s)""",
                        (int(vehicle_id), staff_id, session["user_id"])
                    )
                flash("Staff account created.", "success")
            except Error:
                flash("Could not create staff account. Email may already exist.", "error")
        return redirect(url_for("staff"))
    return render_template("staff.html", vehicles=get_visible_vehicles(),
        staff_members=fetch_all("SELECT user_id, full_name, email FROM users WHERE role='staff' ORDER BY full_name"))


if __name__ == "__main__":
    app.run(debug=True)


