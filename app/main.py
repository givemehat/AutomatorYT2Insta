import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api.routes_videos import router as videos_router
from app.api.routes_clips import router as clips_router
from app.api.routes_publish import router as publish_router
from app.api.routes_system import router as system_router
from app.services.scheduler import start_scheduler, shutdown_scheduler
from app.services.logger import log_event

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Lifecycle
    settings.ensure_directories()
    init_db()
    log_event("INFO", "system", "Database initialized and schema verified.")
    start_scheduler()
    log_event("INFO", "system", f"AutomatorYT2Insta server online in [{settings.AUTOMATION_MODE}] mode.")
    yield
    # Shutdown Lifecycle
    shutdown_scheduler()
    log_event("INFO", "system", "AutomatorYT2Insta server shut down cleanly.")

app = FastAPI(
    title="AutomatorYT2Insta — AI Content Automation Engine",
    version="2.0.0",
    description="Production-grade AI-powered YouTube to Instagram Reels repurposing pipeline.",
    lifespan=lifespan
)

# Open CORS for local and proxy web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local media directory for in-browser video playback & Instagram Graph API fetching
app.mount("/media", StaticFiles(directory=settings.STORAGE_DIR), name="media")

# Setup template renderer for Dashboard
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "dashboard", "templates"))

# Include API routers
app.include_router(videos_router)
app.include_router(clips_router)
app.include_router(publish_router)
app.include_router(system_router)

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Renders the administrative web dashboard UI."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"settings": settings}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
