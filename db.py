import sqlite3
import pandas as pd

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

def get_current_balance():
    df = fetch_transactions()
    print(sum(df["amount"]))
    return sum(df["amount"])