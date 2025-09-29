import sqlite3
import pandas as pd
import exchange_functions as exchange
from datetime import datetime

DB_FILE = "finances.db"

import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)  # safe for Dash callbacks
        self.conn.row_factory = sqlite3.Row  # optional: lets you access by column name

    def query(self, sql, params=None):
        cur = self.conn.cursor()
        cur.execute(sql, params or [])
        rows = cur.fetchall()
        cur.close()
        return rows

    def close(self):
        self.conn.close()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create bookings table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL
            )
        """)

    # Create transactions table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                recipient TEXT NOT NULL,
                date TEXT NOT NULL,
                type TEXT NOT NULL,
                source_csv TEXT NOT NULL,
                excluded INTEGER NOT NULL DEFAULT 0,
                booking_id INTEGER,
                FOREIGN KEY (booking_id) REFERENCES bookings (booking_id),
                UNIQUE (amount, currency, recipient, date, type, source_csv)
            )
        """)
    conn.commit()
    conn.close()

def insert_transaction(amount, currency, recipient, date, type, source_csv, excluded=0, booking_id=None) -> bool:
    added = False
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO transactions (amount, currency, recipient, date, type, source_csv, excluded, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (amount, currency, recipient, date, type, source_csv, excluded, booking_id))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Duplicates
        pass
    finally:
        conn.close()
        print(added)
        return added

def query_db_read(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def fetch_transactions():
    return query_db_read("SELECT * FROM transactions")


def create_booking():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Insert a new booking with current timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO bookings (date) VALUES (?)", (now,))
        conn.commit()
        # Get the id of the newly created booking
        booking_id = cursor.lastrowid
        return booking_id
    finally:
        conn.close()
        
def select_transactions_from_booking(selected_booking_id):
    """
    :param selected_booking_id: which booking transactions to retrieve
    :return: returns transactions corresponding to booking_id
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
                        SELECT transaction_id, date, amount, currency, recipient, type, excluded,booking_id
                        FROM transactions
                        WHERE booking_id = ?
                        ORDER BY date ASC
                    """, (selected_booking_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_bookings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT booking_id, date FROM bookings ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_available_booking_id():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='bookings'")
    row = cursor.fetchone()
    if row is None:
        next_id = 1
    else:
        next_id = row[0] + 1
    return next_id


def get_current_balance(target_currency):  # TEST
    total_balance = 0
    for source_currency, amount in get_balance_per_currency():
        total_balance += exchange.convert_to_currency(source_currency,target_currency, amount)
    return total_balance

def get_balance_per_currency(): # TEST
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

def get_balance_for_common(target_currency): # TEST
    balance_in_common = [(source_currency,exchange.convert_to_currency(source_currency, target_currency, amount)) for source_currency, amount in get_balance_per_currency()]
    return balance_in_common

