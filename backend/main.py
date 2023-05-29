from fastapi import FastAPI
from backend.routers import beers
from backend.database import engine

app = FastAPI()


app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(stock.router)

if engine.connect():
    print("Database connection established")
