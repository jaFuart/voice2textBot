from app.handlers.start import router as start_router
from app.handlers.voice import router as voice_router
from app.handlers.payments import router as payments_router

__all__ = [
    "start_router",
    "voice_router",
    "payments_router",
]