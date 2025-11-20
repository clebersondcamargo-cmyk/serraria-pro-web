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

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "mude-esta-chave-para-uma-muito-forte-2025")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = sqlite3.connect("serraria.db", check_same_thread=False)
c = conn.cursor()

# Tabelas do sistema
c.executescript('''
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, hashed TEXT);
CREATE TABLE IF NOT EXISTS toras (id INTEGER PRIMARY KEY, data TEXT, fornecedor TEXT, volume REAL, valor REAL);
CREATE TABLE IF NOT EXISTS producao (id INTEGER PRIMARY KEY, data TEXT, tora_volume REAL, tabuas REAL, cavaco REAL, po_serra REAL);
CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, unidade TEXT, estoque REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, data TEXT, cliente TEXT, itens TEXT, total REAL, status TEXT);
CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, descricao TEXT, valor REAL);
''')
conn.commit()

# Usuário admin padrão
c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0 and c.execute(
    "INSERT INTO users (username, hashed) VALUES (?, ?)",
    ("admin", pwd_context.hash("serraria2025"))
) and conn.commit()

from utils.auth import get_current_user, create_token, login_page, login_post, register_page, register_post, logout

app.add_route("/login", login_page, ["GET"])
app.add_route("/login", login_post, ["POST"])
app.add_route("/register", register_page, ["GET"])
app.add_route("/register", register_post, ["POST"])
app.add_route("/logout", logout)

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": user})

# APIs simples (você pode expandir)
@app.post("/api/tora")
async def api_tora(fornecedor: str = Form(), volume: float = Form(), valor: float = Form(), user: str = Depends(get_current_user)):
    c.execute("INSERT INTO toras (data, fornecedor, volume, valor) VALUES (date('now'), ?, ?, ?)", (fornecedor, volume, valor))
    c.execute("INSERT INTO financeiro (data, tipo, descricao, valor) VALUES (date('now'), 'pagar', ?, ?)", (f"Compra tora {fornecedor}", -valor))
    conn.commit()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
