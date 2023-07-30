from sqlalchemy import ForeignKey, Column, Integer, String, Float, DateTime

from backend.database import Base


class Beer(Base):
    __tablename__ = "beers"
    beer_id = Column(Integer, index=True, primary_key=True)
    name = Column(String)
    style = Column(String)
    abv = Column(Float)
    price = Column(Float)


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, index=True, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, index=True, primary_key=True)
    beer_id = Column(Integer, ForeignKey("beers.beer_id"), unique=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    qty = Column(Integer)
    ordered_at = Column(DateTime)
    price = Column(Float)


class Stock(Base):
    __tablename__ = "stock"
    stock_id = Column(Integer, index=True, primary_key=True)
    beer_id = Column(Integer, ForeignKey("beers.beer_id"), unique=True)
    qty_in_stock = Column(Integer)
    date_of_arrival = Column(DateTime)
