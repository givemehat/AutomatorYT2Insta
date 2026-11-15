from app.api.routes_videos import router as videos_router
from app.api.routes_clips import router as clips_router
from app.api.routes_publish import router as publish_router
from app.api.routes_system import router as system_router

__all__ = [
    "videos_router",
    "clips_router",
    "publish_router",
    "system_router"
]
