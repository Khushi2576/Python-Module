import sqlite3
from flask import Flask, request, redirect, url_for, flash, render_template_string

app = Flask(__name__)
app.secret_key = "personal_expense_tracker_secret_key"
DB_NAME = "expense_tracker.db"

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Financial Calculation Helper
def get_financial_summary():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Income'")
    total_income = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Expense'")
    total_expense = cursor.fetchone()[0] or 0.0
    
    balance = total_income - total_expense
    conn.close()
    return total_income, total_expense, balance

# Embedded HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Expense Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #f4f6f9; color: #333; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 20px; color: #1a365d; }
        .summary-cards { display: flex; gap: 20px; margin-bottom: 25px; }
        .card { flex: 1; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .card h3 { font-size: 14px; text-transform: uppercase; color: #666; margin-bottom: 10px; }
        .card p { font-size: 24px; font-weight: bold; }
        .income { color: #2e7d32; }
        .expense { color: #c62828; }
        .balance { color: #1565c0; }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; }
        .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .panel h2 { margin-bottom: 15px; font-size: 18px; color: #2d3748; border-bottom: 2px solid #edf2f7; padding-bottom: 8px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; margin-bottom: 5px; font-size: 13px; font-weight: 600; }
        .form-group input, .form-group select { width: 100%; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; }
        .btn { width: 100%; padding: 10px; background-color: #2b6cb0; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 5px; }
        .btn:hover { background-color: #2c5282; }
        .btn-danger { background-color: #e53e3e; width: auto; padding: 4px 8px; font-size: 12px; }
        .filter-box { display: flex; gap: 10px; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #edf2f7; font-size: 14px; }
        th { background-color: #f7fafc; color: #4a5568; }
        .alert { padding: 10px; background-color: #c6f6d5; color: #22543d; border-radius: 4px; margin-bottom: 15px; text-align: center; }
        .reports-list { list-style: none; }
        .reports-list li { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #e2e8f0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personal Expense Tracker</h1>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="summary-cards">
            <div class="card">
                <h3>Total Income</h3>
                <p class="income">₹{{ "%.2f"|format(total_income) }}</p>
            </div>
            <div class="card">
                <h3>Total Expense</h3>
                <p class="expense">₹{{ "%.2f"|format(total_expense) }}</p>
            </div>
            <div class="card">
                <h3>Current Balance</h3>
                <p class="balance">₹{{ "%.2f"|format(balance) }}</p>
            </div>
        </div>

        <div class="grid">
            <div class="panel">
                <h2>Add Transaction</h2>
                <form action="/add" method="POST">
                    <div class="form-group">
                        <label>Date</label>
                        <input type="date" name="date" required>
                    </div>
                    <div class="form-group">
                        <label>Type</label>
                        <select name="type" required>
                            <option value="Expense">Expense</option>
                            <option value="Income">Income</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Amount (₹)</label>
                        <input type="number" step="0.01" name="amount" placeholder="e.g. 500" required>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category" required>
                            <option value="Food">Food</option>
                            <option value="Travel">Travel</option>
                            <option value="Bills">Bills</option>
                            <option value="Salary">Salary</option>
                            <option value="Shopping">Shopping</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <input type="text" name="description" placeholder="Short description">
                    </div>
                    <button type="submit" class="btn">Add Record</button>
                </form>

                <h2 style="margin-top: 25px;">Expense Category Summary</h2>
                <ul class="reports-list">
                    {% for cat, amt in category_reports %}
                        <li><span>{{ cat }}</span> <strong>₹{{ "%.2f"|format(amt) }}</strong></li>
                    {% else %}
                        <li><span>No expenses recorded yet.</span></li>
                    {% endfor %}
                </ul>
            </div>

            <div class="panel">
                <h2>Transaction History</h2>
                <form action="/" method="GET" class="filter-box">
                    <input type="text" name="search" placeholder="Search description..." value="{{ search_query }}" style="flex: 2; padding: 8px;">
                    <select name="category" style="flex: 1; padding: 8px;">
                        <option value="">All Categories</option>
                        <option value="Food" {% if category_filter=='Food' %}selected{% endif %}>Food</option>
                        <option value="Travel" {% if category_filter=='Travel' %}selected{% endif %}>Travel</option>
                        <option value="Bills" {% if category_filter=='Bills' %}selected{% endif %}>Bills</option>
                        <option value="Salary" {% if category_filter=='Salary' %}selected{% endif %}>Salary</option>
                    </select>
                    <button type="submit" class="btn" style="width: auto; margin:0;">Filter</button>
                </form>

                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in transactions %}
                        <tr>
                            <td>{{ row[1] }}</td>
                            <td><span class="{{ 'income' if row[2] == 'Income' else 'expense' }}">{{ row[2] }}</span></td>
                            <td>{{ row[4] }}</td>
                            <td>₹{{ "%.2f"|format(row[3]) }}</td>
                            <td>
                                <form action="/delete/{{ row[0] }}" method="POST" style="display:inline;">
                                    <button type="submit" class="btn btn-danger" onclick="return confirm('Delete this record?')">Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" style="text-align: center;">No transactions found.</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Routes
@app.route('/', methods=['GET'])
def index():
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if search_query:
        query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
        
    query += " ORDER BY date DESC"
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    
    cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type = 'Expense' GROUP BY category")
    category_reports = cursor.fetchall()
    conn.close()
    
    total_income, total_expense, balance = get_financial_summary()
    
    return render_template_string(
        HTML_TEMPLATE,
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        category_reports=category_reports,
        search_query=search_query,
        category_filter=category_filter
    )

@app.route('/add', methods=['POST'])
def add_transaction():
    date = request.form.get('date')
    trans_type = request.form.get('type')
    amount_str = request.form.get('amount')
    category = request.form.get('category')
    description = request.form.get('description', '')
    
    if not date or not trans_type or not amount_str or not category:
        flash("All mandatory fields must be filled!")
        return redirect(url_for('index'))
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash("Amount must be a positive number!")
            return redirect(url_for('index'))
    except ValueError:
        flash("Invalid amount entered!")
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, type, amount, category, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, trans_type, amount, category, description))
    conn.commit()
    conn.close()
    
    flash("Transaction saved successfully!")
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash("Transaction deleted successfully!")
    return redirect(url_for('index'))

if __name__ == '__main__':
 if __name__ == '__main__':
    app.run(debug=True)