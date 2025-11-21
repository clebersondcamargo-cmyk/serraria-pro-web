from fastapi import Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta

from main import templates, c, conn, pwd_context, SECRET_KEY, ALGORITHM


# ============================================================
#   GERAR TOKEN
# ============================================================
def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================================
#   OBTER USUÁRIO
# ============================================================
async def get_current_user(request: Request):
    token = request.cookies.get("token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ============================================================
#   LOGIN PAGE
# ============================================================
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ============================================================
#   LOGIN POST
# ============================================================
async def login_post(form: OAuth2PasswordRequestForm = Depends()):
    c.execute("SELECT username, hashed FROM users WHERE username=?", (form.username,))
    user = c.fetchone()

    if user and pwd_context.verify(form.password, user[1]):
        response = RedirectResponse("/dashboard", status_code=302)
        token = create_token({"sub": user[0]})
        response.set_cookie("token", token, httponly=True)
        return response

    raise HTTPException(status_code=400, detail="Credenciais inválidas")


# ============================================================
#   LOGOUT
# ============================================================
def logout(request: Request):
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("token")
    return response
