from fastapi import Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from . import templates, c, conn, pwd_context, create_token, get_current_user

def create_token(data: dict):
    return jwt.encode({**data, "exp": datetime.utcnow() + timedelta(days=7)}, "your-secret-here", algorithm="HS256")

async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token: raise HTTPException(401)
    try:
        payload = jwt.decode(token, "your-secret-here", algorithms=["HS256"])
        return payload["sub"]
    except:
        raise HTTPException(401)

def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

async def login_post(form: OAuth2PasswordRequestForm = Depends()):
    c.execute("SELECT username, hashed FROM users WHERE username=?", (form.username,))
    user = c.fetchone()
    if user and pwd_context.verify(form.password, user[1]):
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie("token", create_token({"sub": user[0]}), httponly=True, max_age=604800)
        return response
    raise HTTPException(400, "Credenciais inválidas")

# register_page, register_post e logout semelhantes (copie do exemplo anterior)
