import sqlite3
import pandas as pd
import exchange_functions as exchange
from datetime import datetime

DB_FILE = "finances.db"

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
                UNIQUE (amount, currency, recipient, date, source_csv)
            )
        """)
    conn.commit()
    conn.close()

def insert_transaction(date, recipient, currency, amount, type, source_csv, excluded=0, booking_id=None) -> bool:
    added = False
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO transactions (date, recipient, currency, amount, type, source_csv, excluded, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, recipient, currency, amount, type, source_csv, excluded, booking_id))
        conn.commit()
        added = True
    except sqlite3.IntegrityError:
        # Duplicates
        added = False
        pass
    finally:
        conn.close()

def fetch_transactions():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

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
                        SELECT transaction_id, date, amount, currency, recipient, type, excluded
                        FROM transactions
                        WHERE booking_id = ?
                        ORDER BY date ASC
                    """, (selected_booking_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_available_booking_id():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Database is empty
        if cursor.lastrowid is None:
            return 1
        else:
            # Get latest booking id + 1 for the next booking
            booking_id = cursor.lastrowid + 1
            return booking_id
    finally:
        conn.close()



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

