from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import analysis, auth, holdings, stock
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(holdings.router)
app.include_router(analysis.router)
