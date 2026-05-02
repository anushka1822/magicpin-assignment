from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.database import init_db
from api.routes import router
import models.db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router)
