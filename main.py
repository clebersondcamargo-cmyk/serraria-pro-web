from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
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
    login_page,
    login_post,
    logout
)

# LOGIN
app.add_route("/login", login_page, methods=["GET"])
app.add_route("/login", login_post, methods=["POST"])

# LOGOUT
app.add_route("/logout", logout, methods=["GET"])


# ------------------------------
# ÁREA PROTEGIDA
# ------------------------------
@app.get("/", include_in_schema=False)
async def root(request: Request, user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login")
    return RedirectResponse("/dashboard")


@app.get("/dashboard")
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    if not user:
        return RedirectResponse("/login")

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
