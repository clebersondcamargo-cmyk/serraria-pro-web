from fastapi import Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta

from . import templates, c, conn, pwd_context  

# ===== CONFIGURAÇÕES DO JWT =====
SECRET_KEY = "your-secret-here"
ALGORITHM = "HS256"


# ============================================================
#   GERADOR DE TOKEN
# ============================================================
def create_token(data: dict):
    """Gera token JWT com expiração de 7 dias."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================================
#   OBTÉM USUÁRIO A PARTIR DO COOKIE
# ============================================================
async def get_current_user(request: Request):
    """
    Caso o usuário não esteja logado, retorna None
    — permitindo que a rota redirecione para /login.
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
#   PÁGINA DE LOGIN
# ============================================================
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ============================================================
#   LOGIN (POST)
# ============================================================
async def login_post(form: OAuth2PasswordRequestForm = Depends()):
    """
    Processa login, valida senha e cria cookie com token JWT.
    """
    c.execute("SELECT username, hashed FROM users WHERE username=?", (form.username,))
    user = c.fetchone()

    if user and pwd_context.verify(form.password, user[1]):
        response = RedirectResponse("/dashboard", status_code=302)
        token = create_token({"sub": user[0]})
        response.set_cookie(
            "token",
            token,
            httponly=True,
