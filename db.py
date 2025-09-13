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
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_transaction(date, category, amount, notes):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (date, category, amount, notes) VALUES (?, ?, ?, ?)",
        (date, category, amount, notes)
    )
    conn.commit()
    conn.close()

def fetch_transactions():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df