import sqlite3
import pandas as pd
import exchange_functions as exchange
from datetime import datetime

DB_FILE = "column_names.db"

def init_columns_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    #Create tables for the different name columns
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS amount (
                amount_id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount TEXT,
                UNIQUE (amount)
            )
        """)
    conn.commit()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS currency (
                    currency_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT,
                    UNIQUE (currency)
                )
            """)
    conn.commit()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recipient (
                        recipient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recipient TEXT,
                        UNIQUE (recipient)
                    )
                """)
    conn.commit()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS date (
                        date_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        UNIQUE (date)
                    )
                """)
    conn.commit()

    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS type (
                        type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT,
                        UNIQUE (type)
                    )
                """)
    conn.commit()
    conn.close()


def insert_column_name(tablename, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        if value is not None:
            cursor.execute(f"""
                INSERT OR IGNORE INTO {tablename} ({tablename})
                VALUES (?)
            """, (value,))
            conn.commit()
    finally:
        conn.close()


def fetch_names(tablename):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {tablename}", conn)
    conn.close()
    return df[tablename].tolist()
