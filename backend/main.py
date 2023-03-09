from fastapi import FastAPI
from peewee import *
<<<<<<< HEAD:backend/main.py
from backend.routers import beers, orders
from backend.database import db
from backend.routers import beers, orders, users
from backend.database import db
=======
from routers import beers, orders, users
from database import db
>>>>>>> d1828ba (added users to import from /routers):main.py

app = FastAPI()
app.include_router(beers.router)
app.include_router(orders.router)
app.include_router(users.router)

if db.connect():
    print("Database connection established")
