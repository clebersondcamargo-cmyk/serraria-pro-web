# main.py
from fastapi import FastAPI, Request, Depends, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
import sqlite3
import os

# app config
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# security
SECRET_KEY = os.getenv("SECRET_KEY", "troque-agora-por-uma-chave-secreta")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# sqlite
DB_PATH = "serraria.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    hashed TEXT
);

CREATE TABLE IF NOT EXISTS toras (
    id INTEGER PRIMARY KEY,
    data TEXT,
    fornecedor TEXT,
    volume REAL,
    valor REAL
);

CREATE TABLE IF NOT EXISTS producao (
    id INTEGER PRIMARY KEY,
    data TEXT,
    tora_volume REAL,
    tabuas REAL,
    cavaco REAL,
    po_serra REAL
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    unidade TEXT,
    estoque REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY,
    data TEXT,
    cliente TEXT,
    itens TEXT,
    total REAL,
    status TEXT
);

CREATE TABLE IF NOT EXISTS financeiro (
    id INTEGER PRIMARY KEY,
    data TEXT,
    tipo TEXT,
    descricao TEXT,
    valor REAL
);
''')
conn.commit()

# default admin
admin_exists = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
if admin_exists == 0:
    hashed = pwd_context.hash("serraria2025")
    c.execute("INSERT INTO users (username, hashed) VALUES (?, ?)", ("admin", hashed))
    conn.commit()

# auth helpers
from utils.auth import (
    create_token,
    get_current_user,
)

# ---------- ROUTES ----------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")

# login page
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

# login post
@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    # fetch user
    row = c.execute("SELECT username, hashed FROM users WHERE username=?", (username,)).fetchone()
    if not row:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário ou senha inválidos."})
    stored_username, stored_hash = row
    if not pwd_context.verify(password, stored_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Usuário ou senha inválidos."})

    token = create_token({"sub": stored_username})
    response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie("token", token, httponly=True, max_age=7*24*3600)
    return response

# register page
@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register")
def register_post(request: Request, username: str = Form(...), password: str = Form(...), password2: str = Form(...)):
    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Senhas não conferem."})
    # check exists
    exists = c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if exists:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Usuário já existe."})
    hashed = pwd_context.hash(password)
    c.execute("INSERT INTO users (username, hashed) VALUES (?, ?)", (username, hashed))
    conn.commit()
    # login immediately
    token = create_token({"sub": username})
    response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie("token", token, httponly=True, max_age=7*24*3600)
    return response

# logout
@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("token")
    return response

# dashboard (protected)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    # example simple dashboard
    produtos = c.execute("SELECT id, nome, unidade, estoque FROM produtos").fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "produtos": produtos})
