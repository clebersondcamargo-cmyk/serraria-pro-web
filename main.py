from fastapi import FastAPI, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import sqlite3
import os

# ------------------------------
# FASTAPI CONFIG
# ------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ------------------------------
# SECURITY CONFIG
# ------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "troque-agora")
ALGORITHM = "HS256"

# FIX: Passlib + bcrypt compatível com Render
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ------------------------------
# SQLITE CONFIG
# ------------------------------
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

# ------------------------------
# ADMIN DEFAULT
# ------------------------------
# FIX: bcrypt > 72 bytes bug na versão nova
admin_exists = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]

if admin_exists == 0:
    hashed = pwd_context.hash("serraria2025")
    c.execute(
        "INSERT INTO users (username, hashed) VALUES (?, ?)",
        ("admin", hashed)
    )
    conn.commit()

# ------------------------------
# AUTH ROUTES
# ------------------------------
from utils.auth import (
    get_current_user,
    create_token,
    login_page,
    login_post,
    register_page,
    register_post,
    logout
)

app.add_route("/login", login_page, ["GET"])
app.add_route("/login", login_post, ["POST"])
app.add_route("/register", register_page, ["GET"])
app.add_route("/register", register_p
