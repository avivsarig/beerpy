from fastapi import FastAPI
from peewee_dir.peewee import *
from routers import beers, orders, stock
from database import db

app = FastAPI()
app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(stock.router)

if db.connect():
    print("Database connection established")
