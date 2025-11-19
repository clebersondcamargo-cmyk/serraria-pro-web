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

app = FastAPI(title="Serraria PRO Web")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Segurança
SECRET_KEY = os.getenv("SECRET_KEY", "troque-por-uma-chave-forte-aqui-muito-grande-2025")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Banco de dados
conn = sqlite3.connect("serraria.db", check_same_thread=False)
c = conn.cursor()

# Tabelas
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, hashed_password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS toras (id INTEGER PRIMARY KEY, data TEXT, fornecedor TEXT, volume REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, data TEXT, cliente TEXT, volume REAL, valor REAL)''')
# ... (adicione as outras tabelas que quiser)
conn.commit()

# Criar usuário admin padrão se não existir
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    hashed = pwd_context.hash("serraria2025")
    c.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", ("admin", hashed))
    conn.commit()

def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def get_password_hash(p): return pwd_context.hash(p)
def create_token(data: dict): 
    expire = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(401)
    try:
        payload = jwt.decode(token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        raise HTTPException(401)

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    c.execute("SELECT username, hashed_password FROM users WHERE username=?", (form_data.username,))
    user = c.fetchone()
    if not user or not verify_password(form_data.password, user[1]):
        raise HTTPException(400, detail="Usuário ou senha incorretos")
    token = create_token({"sub": user[0]})
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("access_token", f"Bearer {token}", httponly=True, max_age=604800)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(username: str = Form(), password: str = Form()):
    hashed = get_password_hash(password)
    try:
        c.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (username, hashed))
        conn.commit()
    except:
        raise HTTPException(400, detail="Usuário já existe")
    return RedirectResponse("/login", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "username": user})

@app.get("/logout")
def logout():
    response = RedirectResponse("/login")
    response.delete_cookie("access_token")
    return response

# API de exemplo (você pode adicionar todas as outras)
@app.get("/api/estoque")
async def estoque(user
