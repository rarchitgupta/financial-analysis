from fastapi import FastAPI

from app.routers import stock
from app.db import init_db

app = FastAPI()

app.include_router(stock.router)


@app.on_event("startup")
async def startup():
    await init_db()
