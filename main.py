from fastapi import FastAPI
from peewee_dir.peewee import *
from routers import beers
from database import db

app = FastAPI()
app.include_router(beers.router)

if db.connect():
    print("Database connection established")
