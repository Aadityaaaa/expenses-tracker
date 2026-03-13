import os
import datetime

from cs50 import SQL
from flask import Flask, render_template, redirect, request, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-secret-change-me")
app.config["SESSION_PERMANENT"] = False


# Fix Render's postgres:// URL to postgresql:// (required by SQLAlchemy)
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

db = SQL(database_url)


def init_db():
    """Create tables if they don't exist yet."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            hash TEXT NOT NULL,
            email VARCHAR(255)
        )
    """)
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_username ON users(username)")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_email ON users(email)")
    db.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS protein (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            proteinperdollar REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT NOW(),
            price REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            UNIQUE(user_id, category, month, year)
        )
    """)


init_db()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("email", 400):
            return apology("Enter your email")
        if not request.form.get("username"):
            return apology("Enter an username", 400)
        if not request.form.get("password"):
            return apology("Enter a password", 400)
        if not request.form.get("confirmation"):
            return apology("Re-enter your password", 400)
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("your passwords do not match", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ? OR email = ?",
                          request.form.get("username"), request.form.get("email"))
        if len(rows) > 0:
            if rows[0]["email"] == request.form.get("email"):
                return apology("the email is already taken", 400)
            if rows[0]["username"] == request.form.get("username"):
                return apology("the username is already taken", 400)
        else:
            hash_password = generate_password_hash(request.form.get("password"))
            db.execute("INSERT INTO users (email, username, hash) VALUES (?, ?, ?)",
                       request.form.get("email"), request.form.get("username"), hash_password)

            row = db.execute("SELECT id FROM users WHERE username = ?",
                             request.form.get("username"))

            session["user_id"] = row[0]["id"]
            flash("Welcome! Your account has been registered successfully.", "success")
            return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password"):
            return apology("enter valid credentials", 400)
        else:
            rows = db.execute(
                "SELECT * FROM users WHERE username = ?", request.form.get("username"))
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return apology("Invalid credentials. Try again")
            else:
                session["user_id"] = rows[0]["id"]
                return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/", methods=["POST", "GET"])
@login_required
def index():
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [session["user_id"]]

    filter_option = None
    sort_option = "date-desc"

    entries = db.execute(query, *params)
    if not entries:
        return render_template("index.html", expenses=None, total_spent=None, rows=None, sort_option=None, filter_option=None, no_data=True)

    if request.method == "POST":
        filter_option = request.form.get("filter-option")
        sort_option = request.form.get("sort-option")
        session["filter_option"] = filter_option
        session["sort_option"] = sort_option
    else:
        filter_option = session.get("filter_option", None)
        sort_option = session.get("sort_option", "date-desc")

    end_date = datetime.date.today() + datetime.timedelta(days=1)

    if filter_option is None or filter_option == 'thisYear':
        now = datetime.datetime.today()
        start_date = datetime.date(now.year, 1, 1)
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    if filter_option == "last24hours":
        start_date = end_date - datetime.timedelta(days=1)
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif filter_option == "last7days":
        start_date = end_date - datetime.timedelta(days=7)
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif filter_option == "last30days":
        start_date = end_date - datetime.timedelta(days=30)
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif filter_option == "last365days":
        start_date = end_date - datetime.timedelta(days=365)
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    custom_range = request.form.get("custom")
    if filter_option == "custom" and custom_range:
        start_str, end_str = custom_range.split(" to ")
        start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_str, "%Y-%m-%d").date()
        query = query + " AND date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    if sort_option == "date-asc":
        query = query + " ORDER BY date ASC"
    elif sort_option == "date-desc":
        query = query + " ORDER BY date DESC"
    elif sort_option == "amount-asc":
        query = query + " ORDER BY amount ASC"
    elif sort_option == "amount-desc":
        query = query + " ORDER BY amount DESC"

    ids = db.execute(query, *params)
    expenses = []
    for id in ids:
        expense_data = {"id": id["id"], "category": id["category"], "amount": id["amount"],
                        "description": id["description"], "timestamp": id["date"]}
        expenses.append(expense_data)

    total_query = f"SELECT SUM(amount) AS total FROM ({query}) AS filtered_expenses"
    total_row = db.execute(total_query, *params)
    total_spent = total_row[0]["total"] if total_row[0]["total"] is not None else 0

    category_query = f"SELECT category, SUM(amount) AS total FROM ({query}) AS filtered_expenses GROUP BY category"
    category_rows = db.execute(category_query, *params)

    return render_template("index.html", expenses=expenses, total_spent=total_spent, rows=category_rows, sort_option=sort_option, filter_option=filter_option)


@app.route("/add", methods=["POST", "GET"])
@login_required
def add():
    categories = ["Food & Drinks", "Groceries", "Shopping", "Transport",
                  "Entertainment", "Utilities", "Health & Fitness", "Home"]
    if request.method == "GET":
        return render_template("add.html", edit=False, categories=categories)
    else:
        if not request.form.get("category") or not request.form.get("description") or not request.form.get("amount"):
            return apology("enter all the details correctly")
        amount_str = request.form.get("amount")
        try:
            amount = float(amount_str)
        except (TypeError, ValueError):
            return apology("enter a numerical value")
        else:
            # NOW() replaces SQLite's datetime('now')
            db.execute("INSERT INTO expenses(user_id, category, amount, description, date) VALUES (?, ?, ?, ?, NOW())",
                       session["user_id"], request.form.get("category"), amount, request.form.get("description"))
            return redirect("/")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    categories = ["Food & Drinks", "Groceries", "Shopping", "Transport",
                  "Entertainment", "Utilities", "Health & Fitness", "Home"]
    if request.method == "POST":
        category = request.form.get("category")
        amount = request.form.get("amount")
        description = request.form.get("description")

        if not category or not amount or not description:
            return apology("enter the details correctly")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return apology("enter amount correctly.")
        else:
            db.execute("UPDATE expenses SET category=?, amount=?, description=? WHERE id = ? AND user_id = ?",
                       category, amount, description, id, session["user_id"])
        flash("Expense updated successfully!", "success")
        return redirect("/")
    else:
        rows = db.execute(
            "SELECT * FROM expenses WHERE id = ? AND user_id=?", id, session["user_id"])
        if len(rows) != 1:
            return apology("the expense is not found")
        else:
            expense = rows[0]
            return render_template("add.html", expense=expense, categories=categories, edit=True)


@app.route("/history")
@login_required
def history():
    now = datetime.datetime.now()
    current_year = int(now.year)

    year = int(request.args.get("year", str(current_year)))

    # TO_CHAR replaces SQLite's strftime('%Y', date)
    all_years = db.execute(
        "SELECT DISTINCT TO_CHAR(date, 'YYYY') AS year FROM expenses WHERE user_id = ? AND date IS NOT NULL ORDER BY year DESC", session["user_id"])

    years = []
    for row in all_years:
        if row["year"] is not None:
            years.append(int(row["year"]))

    if year not in years:
        years.insert(0, current_year)

    history = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? ORDER BY date DESC", session["user_id"], str(year))
    if not history:
        return render_template("history.html", history=None, years=None, selected_year=year, no_data=True)

    return render_template("history.html", history=history, years=years, selected_year=year)


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    db.execute("DELETE FROM expenses WHERE user_id = ? AND id = ?",
               session["user_id"], id)
    return redirect("/")


@app.route("/protein", methods=["GET", "POST"])
@login_required
def protein():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        net_weight = request.form.get("net_weight")
        serving_size = request.form.get("serving_size")
        protein_serving_size = request.form.get("protein_serving_size")

        if not name or not price or not net_weight or not serving_size or not protein_serving_size:
            return apology("enter all details correctly")
        try:
            price = float(price)
            net_weight = float(net_weight)
            serving_size = float(serving_size)
            protein_serving_size = float(protein_serving_size)
        except (TypeError, ValueError):
            return apology("enter amount correctly.")

        protein_per_dollar = ((net_weight / serving_size) * protein_serving_size) / price if price and price > 0 else None

        db.execute("INSERT INTO protein (user_id, name, proteinperdollar, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], name, protein_per_dollar, price)
        return redirect("/protein")

    else:
        all_items = db.execute(
            "SELECT * FROM protein WHERE user_id = ? ORDER BY proteinperdollar DESC", session["user_id"])
        return render_template("proteinperdollar.html", all_items=all_items, no_data=len(all_items) == 0)


@app.route("/protein/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_protein(id):
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        net_weight = request.form.get("net_weight")
        serving_size = request.form.get("serving_size")
        protein_serving_size = request.form.get("protein_serving_size")

        if not name or not price or not net_weight or not serving_size or not protein_serving_size:
            return apology("enter all details correctly")
        try:
            price = float(price)
            net_weight = float(net_weight)
            serving_size = float(serving_size)
            protein_serving_size = float(protein_serving_size)
        except (TypeError, ValueError):
            return apology("enter amount correctly.")

        protein_per_dollar = ((net_weight / serving_size) * protein_serving_size) / price if price and price > 0 else None

        db.execute("UPDATE protein SET name= ?, proteinperdollar= ?, price= ? WHERE id= ? AND user_id= ?",
                   name, protein_per_dollar, price, id, session["user_id"])
        flash("Entry updated successfully!", "success")
        return redirect("/protein")

    else:
        protein_to_edit = db.execute(
            "SELECT * FROM protein WHERE id = ? AND user_id = ?", id, session["user_id"])
        if len(protein_to_edit) != 1:
            return apology("the protein entry is not found")
        else:
            all_items = db.execute(
                "SELECT * FROM protein WHERE user_id = ? ORDER BY proteinperdollar DESC", session["user_id"])
        return render_template("proteinperdollar.html", protein_to_edit=protein_to_edit[0], all_items=all_items, no_data=len(all_items) == 0)


@app.route("/protein/delete/<int:id>", methods=["POST"])
@login_required
def delete_protein(id):
    db.execute("DELETE FROM protein WHERE id = ? AND user_id = ?", id, session["user_id"])
    return redirect("/protein")


@app.route("/statistics")
@login_required
def statistics():
    now = datetime.datetime.now()
    current_year = int(now.year)

    year = int(request.args.get("year", str(current_year)))

    all_years = db.execute(
        "SELECT DISTINCT TO_CHAR(date, 'YYYY') AS year FROM expenses WHERE user_id = ? AND date IS NOT NULL ORDER BY year DESC", session["user_id"])

    years = []
    for row in all_years:
        if row["year"] is not None:
            years.append(int(row["year"]))

    if year not in years:
        years.insert(0, current_year)

    monthly_data = db.execute(
        "SELECT TO_CHAR(date, 'MM') AS month, SUM(amount) AS monthly_total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? GROUP BY TO_CHAR(date, 'MM')", session["user_id"], str(year))

    months = []
    totals = []
    for i in range(len(monthly_data)):
        months.append(monthly_data[i]["month"])
        totals.append(monthly_data[i]["monthly_total"])

    current_month = int(datetime.datetime.now().month)

    month_names = ["Jan", "Feb", "Mar", "Apr", "May",
                   "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    row = db.execute(
        "SELECT AVG(monthly_total) AS avg_spending, MAX(monthly_total) AS highest, MIN(monthly_total) AS lowest FROM (SELECT TO_CHAR(date, 'MM') AS month, SUM(amount) AS monthly_total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? GROUP BY TO_CHAR(date, 'MM')) AS monthly", session["user_id"], str(year))

    monthly_average_spending = row[0]["avg_spending"]
    highest_spending = row[0]["highest"]
    lowest_spending = row[0]["lowest"]

    row1 = db.execute(
        "SELECT month, MAX(monthly_total) AS highest FROM (SELECT TO_CHAR(date, 'MM') AS month, SUM(amount) AS monthly_total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? GROUP BY TO_CHAR(date, 'MM')) AS monthly", session["user_id"], str(year))

    if not row1 or row1[0]["month"] is None:
        return render_template("stats.html", years=years, selected_year=year, current_month=current_month, months=months, totals=totals, month_names=month_names, monthly_average_spending=None, highest_spending=None, lowest_spending=None, highest_month_name=None, lowest_month_name=None, no_data=True)

    highest_month_num = int(row1[0]["month"])
    highest_month_name = month_names[highest_month_num - 1]

    row2 = db.execute(
        "SELECT month, MIN(monthly_total) AS lowest FROM (SELECT TO_CHAR(date, 'MM') AS month, SUM(amount) AS monthly_total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? GROUP BY TO_CHAR(date, 'MM')) AS monthly", session["user_id"], str(year))

    if not row2 or row2[0]["month"] is None:
        return render_template("stats.html", years=years, selected_year=year, current_month=current_month, months=months, totals=totals, month_names=month_names, monthly_average_spending=None, highest_spending=None, lowest_spending=None, highest_month_name=None, lowest_month_name=None, no_data=True)

    lowest_month_num = int(row2[0]["month"])
    lowest_month_name = month_names[lowest_month_num - 1]

    return render_template("stats.html", years=years, selected_year=year, current_month=current_month, months=months, totals=totals, month_names=month_names, monthly_average_spending=monthly_average_spending, highest_spending=highest_spending, lowest_spending=lowest_spending, highest_month_name=highest_month_name, lowest_month_name=lowest_month_name)


@app.route("/statistics/bar-graph", methods=["POST"])
@login_required
def bar_graph():
    data = request.get_json()

    month_index = int(data.get("month"))
    year = str(data.get("year"))
    selected_month = f"{month_index:02}"

    category_data = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'YYYY') = ? AND TO_CHAR(date, 'MM') = ? GROUP BY category", session["user_id"], year, selected_month)

    category_labels = []
    category_totals = []
    for row in category_data:
        category_labels.append(row["category"])
        category_totals.append(row["total"])

    return jsonify({"category_labels": category_labels, "category_totals": category_totals})


@app.route("/budget", methods=["POST", "GET"])
@login_required
def budget():
    categories = ["Food & Drinks", "Groceries", "Shopping", "Transport",
                  "Entertainment", "Utilities", "Health & Fitness", "Home"]

    now = datetime.datetime.now()
    month = f"{now.month:02d}"
    year = str(now.year)

    existing_budgets = db.execute(
        "SELECT category, amount from budgets WHERE user_id = ? AND month = ? AND year = ?", session["user_id"], month, year)

    budget_exists = True if len(existing_budgets) > 0 else False

    if request.method == "POST":
        category = request.form.getlist("category[]")
        amount = request.form.getlist("amount[]")

        now = datetime.datetime.now()
        month = f"{now.month:02d}"
        year = str(now.year)

        db.execute("DELETE FROM budgets WHERE user_id =? AND month =? AND year =?",
                   session["user_id"], month, year)
        for i in range(len(category)):
            db.execute("INSERT INTO budgets (user_id, category, amount, month, year) VALUES (?,?,?,?,?) ON CONFLICT (user_id, category, month, year) DO UPDATE SET amount = excluded.amount",
                       session["user_id"], category[i], amount[i], month, year)

        return redirect("/budget")

    return render_template("budget.html", categories=categories, existing_budgets=existing_budgets, budget_exists=budget_exists)


@app.route("/budget/progressbar_data", methods=["POST"])
@login_required
def progressbar_data():
    now = datetime.datetime.now()
    month = f"{now.month:02d}"
    year = str(now.year)

    existing_budgets = db.execute(
        "SELECT category, amount FROM budgets WHERE user_id = ? AND month = ? AND year = ?", session["user_id"], month, year)
    current_spending = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ? AND TO_CHAR(date, 'MM') = ? AND TO_CHAR(date, 'YYYY') = ? GROUP BY category", session["user_id"], month, year)

    category_data = {}

    for row in existing_budgets:
        category_data[row["category"]] = {"budget": row["amount"], "spent": 0}

    for row in current_spending:
        if row["category"] in category_data:
            category_data[row["category"]]["spent"] = row["total"]

    progress_labels = []
    progress_budget = []
    spent = []
    for category, values in category_data.items():
        progress_labels.append(category)
        progress_budget.append(values["budget"])
        spent.append(values["spent"])

    return jsonify({"progress_labels": progress_labels, "progress_budget": progress_budget, "spent": spent})
