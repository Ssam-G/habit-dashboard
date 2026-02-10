import sqlite3

DB_ONE = "habits.db"

def get_db_connection():
    conn = sqlite3.connect(DB_ONE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            goal TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            minutes INTEGER NOT NULL CHECK (minutes > 0),
            note TEXT,
            FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def get_habits():
    conn = get_db_connection()
    habits = conn.execute('SELECT * FROM habits ORDER BY created_at DESC').fetchall()
    conn.close()
    return habits

def get_logs(habit_id):
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs WHERE habit_id = ? ORDER BY date ASC', (habit_id,)).fetchall()
    conn.close()
    return logs

def get_logs_between(start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    logs = conn.execute('SELECT * FROM logs WHERE date BETWEEN ? AND ? ORDER BY date ASC', (start_date, end_date)).fetchall()
    conn.close()
    return logs

def get_logs_between_for_habit(habit_id, start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    logs = conn.execute('SELECT * FROM logs WHERE habit_id = ? AND date BETWEEN ? AND ? ORDER BY date ASC', (habit_id, start_date, end_date)).fetchall()
    conn.close()
    return logs

def get_weekly_minutes_for_habit(habit_id, start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    result = conn.execute('SELECT SUM(minutes) as total_minutes FROM logs WHERE habit_id = ? AND date BETWEEN ? AND ?', (habit_id, start_date, end_date)).fetchone()
    conn.close()
    return result['total_minutes'] if result['total_minutes'] is not None else 0