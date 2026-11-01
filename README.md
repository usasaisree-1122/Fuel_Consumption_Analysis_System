# ⛽ Fuel Consumption Analysis System

A web-based application to manage vehicle fuel records, analyse fuel consumption, calculate mileage, and monitor fuel expenses through an interactive dashboard.

## ✨ Features

- User registration and secure login.
- Role-based access for Fleet Managers, Individual Owners, and Staff.
- Vehicle management and staff assignments.
- Fuel entry management with mileage and cost calculations.
- Invalid fuel and odometer reading detection.
- Interactive dashboard with data visualisations.
- PDF and Excel report generation.
- Restricted access to assigned vehicle records.

## 🛠️ Technologies Used

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Data Analysis:** Pandas
- **Visualisation:** Matplotlib
- **Reports:** ReportLab, OpenPyXL

## 📂 Project Structure

```text
Fuel_Consumption_Analysis_System/
│
├── app.py
├── analytics.py
├── calculations.py
├── visualizations.py
├── db_connection.py
├── fuel_consumption_db.sql
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── staff.html
│   ├── vehicles.html
│   ├── fuel_entries.html
│   ├── invalid_readings.html
│   └── reports.html
│
├── static/
│   └── images/
│
└── README.md
```

## ⚙️ Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/usasaisree-1122/Fuel_Consumption_Analysis_System.git
```

**2. Navigate to the project folder**

```bash
cd Fuel_Consumption_Analysis_System
```

**3. Install dependencies**

```bash
pip install flask mysql-connector-python pandas matplotlib reportlab openpyxl
```

**4. Configure the database**

- Start your MySQL server.
- Import `fuel_consumption_db.sql`.
- Configure your database credentials in `db_connection.py`.

**5. Run the application**

```bash
python app.py
```

Open your browser and visit:

`http://127.0.0.1:5000/`

## 👥 User Roles

| Role | Access |
|---|---|
| Fleet Manager | Manage all vehicles, staff, fuel records and reports |
| Individual Owner | Manage own vehicles and fuel records |
| Staff | Access assigned vehicles and their fuel records |

## 🎯 Objective

To provide an efficient system for tracking vehicle fuel consumption, analysing mileage, monitoring expenses, identifying invalid readings, and improving fleet management.

## 👨‍💻 Author

**Usa Sai Sree**

GitHub: [@usasaisree-1122](https://github.com/usasaisree-1122)

---

⭐ If you find this project useful, consider giving the repository a star!

**Fuel Consumption Analysis System — Smarter Fuel Tracking, Better Fleet Management.**