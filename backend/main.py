from fastapi import FastAPI
from backend.routers import beers, orders, stock, users
from backend.migrator import migrator

app = FastAPI()


app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(stock.router)

app.include_router(migrator.router)
