from fastapi import FastAPI
from peewee import *
from routers import beers, orders
from database import db

app = FastAPI()
app.include_router(beers.router)
app.include_router(orders.router)

if db.connect():
    print("Database connection established")
