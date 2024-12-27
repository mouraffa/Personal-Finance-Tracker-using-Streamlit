import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

# Get the current directory
current_dir = Path(__file__).parent.parent
DB_PATH = current_dir / 'data' / 'transactions.db'

def init_db():
    """Initialize the database and create the data directory if it doesn't exist"""
    try:
        # Create data directory if it doesn't exist
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create tables with proper IDs
        c.execute('''CREATE TABLE IF NOT EXISTS transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT NOT NULL,
                      type TEXT NOT NULL,
                      category TEXT NOT NULL,
                      amount REAL NOT NULL,
                      comment TEXT NOT NULL)''')
                      
        c.execute('''CREATE TABLE IF NOT EXISTS fixed_transactions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      start_date TEXT NOT NULL,
                      type TEXT NOT NULL,
                      category TEXT NOT NULL,
                      amount REAL NOT NULL,
                      comment TEXT NOT NULL,
                      last_generated_date TEXT)''')
        
        # Create indices for better performance
        c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_date 
                     ON transactions(date)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_type 
                     ON transactions(type)''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_category 
                     ON transactions(category)''')
                      
        conn.commit()
        conn.close()
        
        # Run migration to ensure schema is up to date
        migrate_database()
        
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")

def save_transaction(date, trans_type, category, amount, comment):
    """Save a new transaction to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (date, type, category, amount, comment) VALUES (?,?,?,?,?)", 
                  (date, trans_type, category, amount, comment))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except Exception as e:
        st.error(f"Error saving transaction: {str(e)}")
        return None

def save_fixed_transaction(start_date, trans_type, category, amount, comment):
    """Save a new fixed transaction to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO fixed_transactions 
                    (start_date, type, category, amount, comment, last_generated_date) 
                    VALUES (?,?,?,?,?,?)""", 
                  (start_date, trans_type, category, amount, comment, start_date))
        new_id = c.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except Exception as e:
        st.error(f"Error saving fixed transaction: {str(e)}")
        return None

def generate_recurring_transactions():
    """Generate transactions from fixed transactions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all fixed transactions
        c.execute("""SELECT id, start_date, type, category, amount, comment, last_generated_date 
                    FROM fixed_transactions""")
        fixed_transactions = c.fetchall()
        
        today = datetime.now().date()
        
        for ft in fixed_transactions:
            # Unpack the tuple into named variables for clarity
            (ft_id, start_date, ft_type, category, amount, 
             comment, last_generated) = ft
            
            # Convert dates to datetime.date objects
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            last = datetime.strptime(last_generated, '%Y-%m-%d').date()
            
            # Generate monthly transactions up to today
            current_date = last
            while (current_date + timedelta(days=32)).replace(day=start.day) <= today:
                next_date = (current_date + timedelta(days=32)).replace(day=start.day)
                
                # Add the transaction
                c.execute("""INSERT INTO transactions 
                           (date, type, category, amount, comment)
                           VALUES (?,?,?,?,?)""",
                         (next_date.strftime('%Y-%m-%d'), ft_type, category, 
                          amount, comment))
                
                # Update last generated date
                c.execute("""UPDATE fixed_transactions 
                           SET last_generated_date = ? 
                           WHERE id = ?""",
                         (next_date.strftime('%Y-%m-%d'), ft_id))
                
                current_date = next_date
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error generating recurring transactions: {str(e)}")


def get_transactions():
    """Retrieve all transactions from the database"""
    try:
        # First generate any pending recurring transactions
        generate_recurring_transactions()
        
        conn = sqlite3.connect(DB_PATH)
        # Only select id once and don't include rowid
        df = pd.read_sql_query("SELECT id, date, type, category, amount, comment FROM transactions", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error retrieving transactions: {str(e)}")
        return pd.DataFrame(columns=['id', 'date', 'type', 'category', 'amount', 'comment'])

def init_settings_tables():
    """Initialize the settings tables in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create general settings table
        c.execute('''CREATE TABLE IF NOT EXISTS general_settings
                     (setting_key TEXT PRIMARY KEY,
                      setting_value TEXT NOT NULL)''')
                      
        # Create category thresholds table
        c.execute('''CREATE TABLE IF NOT EXISTS category_thresholds
                     (category TEXT PRIMARY KEY,
                      monthly_limit REAL NOT NULL)''')
        
        # Insert default settings if they don't exist
        c.execute('''INSERT OR IGNORE INTO general_settings (setting_key, setting_value)
                     VALUES ('currency_symbol', '$')''')
        c.execute('''INSERT OR IGNORE INTO general_settings (setting_key, setting_value)
                     VALUES ('currency_position', 'before')''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error initializing settings tables: {str(e)}")

def get_setting(setting_key):
    """Get a single setting value"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT setting_value FROM general_settings WHERE setting_key = ?", (setting_key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        st.error(f"Error retrieving setting: {str(e)}")
        return None

def update_setting(setting_key, setting_value):
    """Update a single setting"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO general_settings (setting_key, setting_value)
                     VALUES (?, ?)''', (setting_key, setting_value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating setting: {str(e)}")
        return False

def get_category_thresholds():
    """Get all category thresholds"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM category_thresholds", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error retrieving category thresholds: {str(e)}")
        return pd.DataFrame(columns=['category', 'monthly_limit'])

def update_category_threshold(category, monthly_limit):
    """Update or insert a category threshold"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO category_thresholds (category, monthly_limit)
                     VALUES (?, ?)''', (category, monthly_limit))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating category threshold: {str(e)}")
        return False

def check_category_threshold(category, amount, date):
    """Check if a transaction would exceed the monthly threshold"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get the threshold for this category
        c.execute("SELECT monthly_limit FROM category_thresholds WHERE category = ?", (category,))
        threshold = c.fetchone()
        
        if threshold:
            # Calculate the start of the current month
            transaction_date = datetime.strptime(date, '%Y-%m-%d')
            month_start = transaction_date.replace(day=1).strftime('%Y-%m-%d')
            
            # Get total spending for this category this month
            c.execute("""
                SELECT SUM(ABS(amount))
                FROM transactions
                WHERE category = ?
                AND type = 'Expense'
                AND date >= ?
                AND date <= ?
            """, (category, month_start, date))
            
            current_total = c.fetchone()[0] or 0
            conn.close()
            
            # Check if adding this amount would exceed the threshold
            if (current_total + abs(amount)) > threshold[0]:
                return True, threshold[0], current_total
            
        return False, 0, 0
    except Exception as e:
        st.error(f"Error checking category threshold: {str(e)}")
        return False, 0, 0

def update_transaction(transaction_id, date, trans_type, category, amount, comment):
    """Update an existing transaction"""
    try:
        # Convert amount to float and ensure it's negative for expenses
        amount = float(amount)
        if trans_type == "Expense" and amount > 0:
            amount = -amount
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Update the transaction
        c.execute("""UPDATE transactions 
                    SET date = ?,
                        type = ?,
                        category = ?,
                        amount = ?,
                        comment = ?
                    WHERE id = ?""",
                 (date, trans_type, category, amount, str(comment), transaction_id))
        
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    except Exception as e:
        st.error(f"Error updating transaction: {str(e)}")
        return False

def delete_transaction(transaction_id):
    """Delete a transaction by its ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        rows_affected = c.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
    except Exception as e:
        st.error(f"Error deleting transaction: {str(e)}")
        return False

def search_transactions(search_term="", min_amount=None, max_amount=None):
    """Search transactions based on various criteria"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Build the query dynamically
        query = "SELECT *, rowid as id FROM transactions WHERE 1=1"
        params = []
        
        if search_term:
            query += " AND (comment LIKE ? OR category LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if min_amount is not None and min_amount > 0:
            query += " AND ABS(amount) >= ?"
            params.append(min_amount)
        
        if max_amount is not None and max_amount > 0:
            query += " AND ABS(amount) <= ?"
            params.append(max_amount)
        
        # Read the data into a DataFrame
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error searching transactions: {str(e)}")
        return pd.DataFrame()

def generate_monthly_report(year, month):
    """Generate a monthly financial report"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get transactions for the specified month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        query = """
        SELECT *, rowid as id
        FROM transactions 
        WHERE date >= ? AND date < ?
        """
        
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        
        if df.empty:
            return df, {}
        
        # Calculate summary statistics
        summary = {
            'total_income': df[df['type'] == 'Income']['amount'].sum(),
            'total_expenses': abs(df[df['type'] == 'Expense']['amount'].sum()),
            'transaction_count': len(df),
            'category_breakdown': df[df['type'] == 'Expense'].groupby('category')['amount'].sum().abs(),
            'daily_expenses': df[df['type'] == 'Expense'].groupby('date')['amount'].sum().abs()
        }
        
        # Get category thresholds and calculate budget status
        thresholds_df = get_category_thresholds()
        for _, row in thresholds_df.iterrows():
            category = row['category']
            budget = row['monthly_limit']
            spent = abs(df[(df['type'] == 'Expense') & (df['category'] == category)]['amount'].sum())
            
            summary[f'{category}_budget_status'] = {
                'budget': budget,
                'spent': spent,
                'remaining': max(budget - spent, 0),
                'percentage': (spent / budget * 100) if budget > 0 else 0
            }
        
        conn.close()
        return df, summary
    except Exception as e:
        st.error(f"Error generating monthly report: {str(e)}")
        return pd.DataFrame(), {}

# Continuing with generate_yearly_report function...

def generate_yearly_report(year):
    """Generate a yearly financial report"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get transactions for the specified year
        start_date = f"{year}-01-01"
        end_date = f"{year + 1}-01-01"
        
        query = """
        SELECT *, rowid as id
        FROM transactions 
        WHERE date >= ? AND date < ?
        """
        
        df = pd.read_sql_query(query, conn, params=[start_date, end_date])
        
        if df.empty:
            return df, {}
        
        # Convert date to datetime for grouping
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate summary statistics
        summary = {
            'total_income': df[df['type'] == 'Income']['amount'].sum(),
            'total_expenses': abs(df[df['type'] == 'Expense']['amount'].sum()),
            'transaction_count': len(df),
            'monthly_avg_income': df[df['type'] == 'Income']['amount'].sum() / 12,
            'monthly_avg_expenses': abs(df[df['type'] == 'Expense']['amount'].sum()) / 12,
            'category_yearly': df[df['type'] == 'Expense'].groupby('category')['amount'].sum().abs(),
            'monthly_breakdown': df.groupby([df['date'].dt.month, 'type'])['amount'].sum().unstack(),
            'growth_rates': df.groupby(df['date'].dt.month)['amount'].sum().pct_change()
        }
        
        conn.close()
        return df, summary
    except Exception as e:
        st.error(f"Error generating yearly report: {str(e)}")
        return pd.DataFrame(), {}

def get_transaction_by_id(transaction_id):
    """Get a single transaction by its ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT *, rowid as id FROM transactions WHERE id = ?"
        df = pd.read_sql_query(query, conn, params=[transaction_id])
        conn.close()
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.error(f"Error retrieving transaction: {str(e)}")
        return None

def save_budget(category, amount):
    """Save or update a budget amount for a category (alias for update_category_threshold)"""
    return update_category_threshold(category, amount)

def get_budget(category):
    """Get the budget amount for a category"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT monthly_limit FROM category_thresholds WHERE category = ?", (category,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        st.error(f"Error retrieving budget: {str(e)}")
        return 0

def get_monthly_category_spending(category, year, month):
    """Get total spending for a category in a specific month"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Calculate date range for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        query = """
        SELECT SUM(ABS(amount)) as total
        FROM transactions
        WHERE category = ?
        AND type = 'Expense'
        AND date >= ?
        AND date < ?
        """
        
        df = pd.read_sql_query(query, conn, params=[category, start_date, end_date])
        conn.close()
        
        return float(df['total'].iloc[0]) if not df['total'].isna().iloc[0] else 0.0
    except Exception as e:
        st.error(f"Error getting monthly category spending: {str(e)}")
        return 0.0

def get_budget_summary():
    """Get a summary of all budgets and current spending"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get current month and year
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Get all categories and their budgets
        budgets_df = pd.read_sql_query("SELECT * FROM category_thresholds", conn)
        
        summary = {}
        for _, row in budgets_df.iterrows():
            category = row['category']
            budget = row['monthly_limit']
            spent = get_monthly_category_spending(category, year, month)
            
            summary[category] = {
                'budget': budget,
                'spent': spent,
                'remaining': max(budget - spent, 0),
                'percentage': (spent / budget * 100) if budget > 0 else 0
            }
        
        conn.close()
        return summary
    except Exception as e:
        st.error(f"Error getting budget summary: {str(e)}")
        return {}

def migrate_database():
    """Migrate database to new schema if needed"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check transactions table
        cursor = c.execute('PRAGMA table_info(transactions)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'id' not in columns:
            # Create new transactions table with id
            c.execute('''CREATE TABLE IF NOT EXISTS transactions_new
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          date TEXT NOT NULL,
                          type TEXT NOT NULL,
                          category TEXT NOT NULL,
                          amount REAL NOT NULL,
                          comment TEXT NOT NULL)''')
            
            # Copy data from old table to new table
            c.execute('''INSERT INTO transactions_new (date, type, category, amount, comment)
                         SELECT date, type, category, amount, comment FROM transactions''')
            
            # Drop old table and rename new table
            c.execute('DROP TABLE IF EXISTS transactions')
            c.execute('ALTER TABLE transactions_new RENAME TO transactions')
            
            # Recreate indices
            c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_date 
                         ON transactions(date)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_type 
                         ON transactions(type)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_transactions_category 
                         ON transactions(category)''')
        
        # Check fixed_transactions table
        cursor = c.execute('PRAGMA table_info(fixed_transactions)')
        ft_columns = [row[1] for row in cursor.fetchall()]
        
        if 'id' not in ft_columns:
            # Create new fixed_transactions table with id
            c.execute('''CREATE TABLE IF NOT EXISTS fixed_transactions_new
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          start_date TEXT NOT NULL,
                          type TEXT NOT NULL,
                          category TEXT NOT NULL,
                          amount REAL NOT NULL,
                          comment TEXT NOT NULL,
                          last_generated_date TEXT)''')
            
            # Copy data from old table to new table if it exists
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fixed_transactions'")
            if c.fetchone():
                c.execute('''INSERT INTO fixed_transactions_new 
                            (start_date, type, category, amount, comment, last_generated_date)
                            SELECT start_date, type, category, amount, comment, last_generated_date 
                            FROM fixed_transactions''')
                
                # Drop old table
                c.execute('DROP TABLE IF EXISTS fixed_transactions')
            
            c.execute('ALTER TABLE fixed_transactions_new RENAME TO fixed_transactions')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error migrating database: {str(e)}")
        return False