# Fuel Consumption Analysis System

## Project Objective
To record and analyze vehicle fuel consumption, calculate mileage and fuel expenses, compare vehicle performance, and present useful insights through graphs and reports.

## Technologies Used
- Python
- Flask
- MySQL
- Pandas
- NumPy
- Matplotlib
- HTML and CSS

## Main Features
- Add and manage vehicle details.
- Record fuel entries and odometer readings.
- Calculate distance travelled and vehicle mileage.
- Calculate total fuel expenses and cost per kilometre.
- Compare mileage across vehicles.
- Analyze monthly fuel consumption and expenses.
- Display charts and reports for better data visualization.
- Maintain an Invalid Readings Log for rejected fuel-entry submissions.

## Project Files
- `app.py` – Main Flask application and routes.
- `db_connection.py` – MySQL database connection.
- `calculations.py` – Fuel and mileage calculation functions.
- `analytics.py` – Fuel consumption data analysis.
- `visualizations.py` – Generates charts and graphs.
- `templates/` – HTML pages for the application.
- `static/images/` – Generated charts and visualizations.
- `test_calculations.py` – Basic calculation tests.
- `README.md` – Project documentation.

## How to Run
1. Open the project in PyCharm.
2. Install the required Python libraries.
3. Configure the MySQL database and connection settings.
4. Ensure the required database and tables are created.
5. Run `app.py`.
6. Open the local URL displayed in the terminal in your browser.

## Expected Result
The system helps users monitor vehicle mileage, understand fuel expenses, compare vehicle performance, analyze monthly fuel consumption, and identify invalid fuel-entry attempts through reports and visualizations.
