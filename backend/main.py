from fastapi import FastAPI
from backend.routers import beers, orders, stock, users


app = FastAPI()

app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(stock.router)
