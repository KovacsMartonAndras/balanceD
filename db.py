import sqlite3
import pandas as pd
import exchange_functions as exchange
DB_FILE = "finances.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(date, description, currency, amount)
        )
    """)
    conn.commit()
    conn.close()

def insert_transaction(date, description, currency, amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (date, description, currency, amount) VALUES (?, ?, ?, ?)",
            (date, description, currency, amount)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Duplicate detected, ignore
        pass
    finally:
        conn.close()

def fetch_transactions():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

def get_current_balance(target_currency):
    total_balance = 0
    for source_currency, amount in get_balance_per_currency():
        total_balance += exchange.convert_to_currency(source_currency,target_currency, amount)
    return total_balance

def get_balance_per_currency():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT currency, SUM(amount) as balance
        FROM transactions
        GROUP BY currency
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_balance_for_common(target_currency):
    balance_in_common = [(source_currency,exchange.convert_to_currency(source_currency, target_currency, amount)) for source_currency, amount in get_balance_per_currency()]
    return balance_in_common

