import sqlite3
from datetime import date as dt_date, timedelta

DB_NAME = "habits.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
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
    result = conn.execute('SELECT SUM(minutes) as total_habit_minutes FROM logs WHERE habit_id = ? AND date BETWEEN ? AND ?', (habit_id, start_date, end_date)).fetchone()
    conn.close()
    return result['total_habit_minutes'] if result['total_habit_minutes'] is not None else 0

def get_total_weekly_minutes(start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    result = conn.execute('SELECT COALESCE(SUM(minutes), 0) as total_minutes FROM logs WHERE date BETWEEN ? AND ?', (start_date, end_date)).fetchone()
    conn.close()
    return result['total_minutes'] if result['total_minutes'] is not None else 0

def get_longest_log(start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    result = conn.execute('''
        SELECT logs.habit_id, habits.name as habit_name, logs.minutes, logs.date 
        FROM logs
        JOIN habits ON habits.id = logs.habit_id
        WHERE logs.date 
        BETWEEN ? AND ? 
        ORDER BY logs.minutes DESC
        LIMIT 1
    ''', (start_date, end_date)).fetchone()
    conn.close()
    return result if result else None

def best_habit_of_week(start_date, end_date):
    conn = get_db_connection()
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()
    result = conn.execute('''
        SELECT habits.id, habits.name, COALESCE(SUM(logs.minutes), 0) as total_minutes
        FROM logs
        JOIN habits ON habits.id = logs.habit_id
        WHERE logs.date BETWEEN ? AND ?
        GROUP BY habits.id
        ORDER BY total_minutes DESC
        LIMIT 1
    ''', (start_date, end_date)).fetchone()
    conn.close()
    return result if result else None

def get_current_streak_for_habit(habit_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT DISTINCT date 
        FROM logs 
        WHERE habit_id = ? 
        ORDER BY date DESC
    ''', (habit_id,)).fetchall()
    conn.close()

    if not rows:
        return 0
    
    dates = [dt_date.fromisoformat(row['date']) for row in rows]

    today = dt_date.today()
    yesterday = today - timedelta(days=1)

    if dates[0] < yesterday:
        return 0
    
    streak = 1
    current_day = dates[0]

    for next_day in dates[1:]:
        if current_day - next_day == timedelta(days=1):
            streak += 1
            current_day = next_day
        else:
            break

    return streak

def get_longest_streak():
    habits = get_habits()
    
    if not habits:
        return 0
    
    longest = None
    longest_streak = 0

    for habit in habits:
        streak = get_current_streak_for_habit(habit['id'])
        if streak > longest_streak:
            longest_streak = streak
            longest = habit

    if longest is None:
        return None
    
    return {"habit_id": longest['id'], "habit_name": longest['name'], "streak": longest_streak}
        