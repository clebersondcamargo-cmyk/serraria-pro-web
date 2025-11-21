from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
import sqlite3


# ============================================================
#  CONFIGURAÇÕES GERAIS
# ============================================================

SECRET_KEY = "your-secret-here"
ALGORITHM = "HS256"

# Templates (Render exige caminho absoluto/relativo válido)
templates = Jinja2Templates(directory="templates")

# Banco de dados
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

# Hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
#  GERADOR DE TOKEN
# ============================================================

def create_token(data: dict):
    """Gera token JWT com expiração de 7 dias."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================================
#  OBTÉM USUÁRIO PELO COOKIE
# ============================================================

async def get_current_user(request: Request):
    """
    Retorna o usuário logado ou None.
    Não quebra a aplicação se o token estiver ausente.
    """
    token = request.cookies.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ============================================================
#  PÁGINA DE LOGIN
# ============================================================

def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
