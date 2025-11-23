from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import (
    auth_routes,
    dashboard_routes,
    toras_routes,
    producao_routes,
    produtos_routes,
    vendas_routes,
    financeiro_routes
)

app = FastAPI(title="Serraria PRO", version="1.0.0")

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(auth_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(toras_routes.router)
app.include_router(producao_routes.router)
app.include_router(produtos_routes.router)
app.include_router(vendas_routes.router)
app.include_router(financeiro_routes.router)


@app.get("/")
async def root():
    """
    Página inicial redireciona para login.
    """
    return {"message": "Serraria PRO API – use /login"}
