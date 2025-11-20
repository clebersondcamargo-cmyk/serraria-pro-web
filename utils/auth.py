from fastapi import Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
import sqlite3

# Removido import circular ❌
# from . import templates, c, conn, pwd_context

# Criados localmente ✔
templates = Jinja2Templates(directory="templates")
conn = sqlite3.connect("serraria.db", check_same_thread=False)
c = conn.cursor()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your-secret-here"
ALGORITHM = "HS256"


def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token não encontrado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


async def login_post(form: OAuth2PasswordRequestForm = Depends()):
    c.execute("SELECT username, hashed FROM users WHERE username=?", (form.username,))
    user = c.fetchone()

    if not user or not pwd_context.verify(form.password, user[1]):
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    token = create_token({"sub": user[0]})
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("token", token, httponly=True, max_age=604800)
    return response


def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


async def register_post(username: str = Form(...), password: str = Form(...)):
    hashed = pwd_context.hash(password)
    try:
        c.execute("INSERT INTO users (username, hashed) VALUES (?, ?)", (username, hashed))
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    return RedirectResponse("/login", status_code=302)


async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("token")
    return response
