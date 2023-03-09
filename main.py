from fastapi import FastAPI
from peewee import *
from routers import beers, orders, users
from database import db

app = FastAPI()
app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)

if db.connect():
    print("Database connection established")
