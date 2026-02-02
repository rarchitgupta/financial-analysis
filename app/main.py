from fastapi import FastAPI

from app.routers import stock

app = FastAPI()

app.include_router(stock.router)
