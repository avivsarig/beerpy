from fastapi import FastAPI
from peewee import *
from backend.routers import beers, orders
from backend.database import db
from backend.routers import beers, orders, users
from backend.database import db

app = FastAPI()
app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)

if db.connect():
    print("Database connection established")
