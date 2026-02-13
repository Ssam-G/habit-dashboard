from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .db import *
from datetime import date as dt_date, timedelta

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_current_week_start():
    today = dt_date.today()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week

def get_week_end():
    start_of_week = get_current_week_start()
    end_of_week = start_of_week + timedelta(days=6)
    return end_of_week

def get_month_start():
    today = dt_date.today()
    start_of_month = dt_date(today.year, today.month, 1)
    return start_of_month

def get_month_end():
    today = dt_date.today()
    if today.month == 12:
        next_month = dt_date(today.year + 1, 1, 1)
    else:
        next_month = dt_date(today.year, today.month + 1, 1)
    end_of_month = next_month - timedelta(days=1)
    print(f"Month end: {end_of_month}")
    return end_of_month


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    habits = get_habits()

    longest_streak = get_longest_streak()
    total_minutes =get_total_weekly_minutes(start_date=get_current_week_start(), end_date=get_week_end())
    best_habit = best_habit_of_week(start_date=get_current_week_start(), end_date=get_week_end())

    return templates.TemplateResponse("index.html", {"request": request, "habits": habits, "total_minutes": total_minutes, "longest_streak": longest_streak, "best_habit": best_habit})

@app.get("/habit/{habit_id}", response_class=HTMLResponse)
def habit_detail(request: Request, habit_id: int):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ?', (habit_id,)).fetchone()
    conn.close()

    if habit is None:
        return RedirectResponse("/", status_code=303)
    
    start_date = get_current_week_start()
    end_date = get_week_end()

    logs = get_logs_between_for_habit(habit_id, start_date, end_date)

    weekly_minutes = get_weekly_minutes_for_habit(habit_id, start_date, end_date)   

    streak = get_current_streak_for_habit(habit_id)

    return templates.TemplateResponse("habit.html", {"request": request, "habit": habit, "logs": logs, "weekly_minutes": weekly_minutes, "streak": streak, "start_date": start_date, "end_date": end_date})

@app.get("/add_habit_page", response_class=HTMLResponse)
def add_habit_page(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

@app.post("/add_habit", response_class=HTMLResponse)
def add_habit(request: Request, name: str = Form(...), goal: str = Form(None)):
    if goal == "":
        goal = None

    conn = get_db_connection()
    conn.execute('INSERT INTO habits (name, goal) VALUES (?, ?)', (name, goal))
    conn.commit()
    conn.close()

    return RedirectResponse("/", status_code=303)

@app.post("/add_log/{habit_id}", response_class=HTMLResponse)
def add_log(request: Request, habit_id, date: str = Form(None), minutes: int = Form(...), note: str = Form(None)):
    if note == "":
        note = None

    if not date:
        date = dt_date.today().isoformat()

    conn = get_db_connection()
    conn.execute('INSERT INTO logs (habit_id, date, minutes, note) VALUES (?, ?, ?, ?)', (habit_id, date, minutes, note))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/habit/{habit_id}", status_code=303)

@app.get("/edit_page/{habit_id}/{log_id}", response_class=HTMLResponse)
def edit_page(request: Request, habit_id, log_id):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ?', (habit_id,)).fetchone()
    log = conn.execute('SELECT * FROM logs WHERE id = ?', (log_id,)).fetchone()
    conn.close()

    return templates.TemplateResponse("edit.html", {"request": request, "habit": habit, "log": log})

@app.post("/edit_log/{habit_id}/{log_id}", response_class=HTMLResponse)
def edit_log(request: Request, habit_id, log_id, date: str = Form(None), minutes: int = Form(...), note: str = Form(None)):
    conn = get_db_connection()
    log = conn.execute('SELECT * FROM logs WHERE id = ?', (log_id,)).fetchone()
    conn.close()

    if log is None:
        return RedirectResponse(f"/habit/{habit_id}", status_code=303)

    date = log['date'] if date is None else date
    minutes = log['minutes'] if minutes is None else minutes
    note = log['note'] if note is None else note

    conn = get_db_connection()
    conn.execute('UPDATE logs SET date = ?, minutes = ?, note = ? WHERE id = ?', (date, minutes, note, log_id))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/habit/{habit_id}", status_code=303)

@app.post("/delete_log/{habit_id}/{log_id}", response_class=HTMLResponse)
def delete_log(habit_id: int, log_id: int):
    conn = get_db_connection()
    conn.execute('DELETE FROM logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/habit/{habit_id}", status_code=303)