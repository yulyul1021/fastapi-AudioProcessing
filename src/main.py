from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .audio import audio_router
from .user import user_router


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(audio_router.router)
app.include_router(user_router.router)
