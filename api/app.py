from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes.auth import router as auth_router
from api.routes.user_routes import router as user_router
from api.routes.target_routes import router as target_router
from api.routes.group_routes import router as group_router
from api.routes.scan_routes import router as scan_router
from api.routes.report_routes import router as report_router
from api.routes.ticket_routes import router as ticket_router

app = FastAPI(title="VulnScanner API")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(target_router)
app.include_router(group_router)
app.include_router(scan_router)
app.include_router(report_router)
app.include_router(ticket_router)

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

@app.get("/login")
def serve_login():
    return FileResponse("frontend/login.html")
