from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .db import get_habits
from .db import get_logs
from .db import get_logs_between
from .db import get_db_connection
from .db import get_weekly_minutes_for_habit
from .db import init_db
from datetime import date, timedelta

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_current_week_start():
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week

def get_week_end():
    start_of_week = get_current_week_start()
    end_of_week = start_of_week + timedelta(days=6)
    return end_of_week

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    habits = get_habits()
    logs = get_logs_between(start_date=get_current_week_start(), end_date=get_week_end())

    return templates.TemplateResponse("index.html", {"request": request, "habits": habits, "logs": logs})

@app.get("/habit/{habit_id}", response_class=HTMLResponse)
def habit_detail(request: Request, habit_id: int):
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ?', (habit_id,)).fetchone()
    conn.close()

    if habit is None:
        return RedirectResponse("/", status_code=303)

    logs = get_logs(habit_id)

    weekly_minutes = get_weekly_minutes_for_habit(habit_id, start_date=get_current_week_start(), end_date=get_week_end())   

    return templates.TemplateResponse("habit.html", {"request": request, "habit": habit, "logs": logs, "weekly_minutes": weekly_minutes})

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

    if date == "":
        date = date.today().isoformat()

    conn = get_db_connection()
    conn.execute('INSERT INTO logs (habit_id, date, minutes, note) VALUES (?, ?, ?, ?)', (habit_id, date, minutes, note))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/habit/{habit_id}", status_code=303)
    