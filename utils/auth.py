from fastapi import Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta

from . import templates, c, conn, pwd_context  

SECRET_KEY = "your-secret-here"
ALGORITHM = "HS256"


def create_token(data: dict):
    """Gera token JWT com expiração de 7 dias."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request):
    """Obtém usuário a partir do token salvo no cookie."""
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Token não encontrado")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def login_page(request: Request):
    """Retorna a página de login."""
    return templates.TemplateResponse("login.html", {"request": request})


async def login_post(form: OAuth2PasswordRequestForm = Depends()):
    """Processa login, valida senha e cria token."""
    c.execute("SELECT username, hashed FROM users WHERE username=?", (form.username,))
    user = c.fetchone()

    if
