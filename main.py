from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import sqlite3
import os

# ------------------------------
# CONFIGURAÇÃO BÁSICA
# ------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SECRET_KEY = os.getenv("SECRET_KEY", "troque-agora-por-uma-chave-segura")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_PATH = "serraria.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# ------------------------------
# CRIAÇÃO DE TABELAS (se não existir)
# ------------------------------
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
# CRIAÇÃO DE USUÁRIO ADMIN (se vazio)
# ------------------------------
admin_exists = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
if admin_exists == 0:
    hashed = pwd_context.hash("serraria2025")
    c.execute("INSERT INTO users (username, hashed) VALUES (?, ?)", ("admin", hashed))
    conn.commit()

# ------------------------------
# UTIL: Token JWT
# ------------------------------
def create_token(data: dict):
    """Gera token JWT com expiração (dias)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ------------------------------
# DEPENDENCY: usuário atual
# ------------------------------
async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")

# ------------------------------
# ROTAS AUTH (GET/POST)
# ------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def login_post(request: Request):
    # recebendo form (nome de campo 'username' e 'password' no template)
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "")

    if not username or not password:
        context = {"request": request, "error": "Informe usuário e senha."}
        return templates.TemplateResponse("login.html", context, status_code=400)

    row = c.execute("SELECT username, hashed FROM users WHERE username=?", (username,)).fetchone()
    if not row or not pwd_context.verify(password, row[1]):
        context = {"request": request, "error": "Usuário ou senha inválidos."}
        return templates.TemplateResponse("login.html", context, status_code=401)

    token = create_token({"sub": row[0]})
    response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    # cookie seguro: HttpOnly (não acessível via JS), ajuste secure=True em produção com HTTPS
    response.set_cookie("token", token, httponly=True, max_age=TOKEN_EXPIRE_DAYS*24*3600, samesite="lax")
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None, "success": None})

@app.post("/register")
async def register_post(request: Request):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "")
    password2 = form.get("password2", "")

    if not username or not password or not password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Preencha todos os campos."}, status_code=400)

    if password != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "As senhas não conferem."}, status_code=400)

    # checar usuário existente
    exists = c.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    if exists:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Nome de usuário já existe."}, status_code=400)

    hashed = pwd_context.hash(password)
    c.execute("INSERT INTO users (username, hashed) VALUES (?, ?)", (username, hashed))
    conn.commit()
    return templates.TemplateResponse("register.html", {"request": request, "success": "Cadastro realizado com sucesso. Faça login."})

@app.get("/logout")
async def logout():
    response = RedirectResponse("/login")
    response.delete_cookie("token")
    return response

# ------------------------------
# ROTA PROTEGIDA DE EXEMPLO
# ------------------------------
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login")
    # exemplo de dados simples
    stats = {
        "toras": c.execute("SELECT COUNT(*) FROM toras").fetchone()[0],
        "produtos": c.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "vendas": c.execute("SELECT COUNT(*) FROM vendas").fetchone()[0],
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "stats": stats})

# ------------------------------
# EXEMPLO: rota pública simples
# ------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}
