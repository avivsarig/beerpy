from pydantic import BaseModel
from datetime import date, datetime


# Beer models
class BeerBase(BaseModel):
    name: str
    style: str
    abv: float
    price: float


class BeerCreate(BeerBase):
    pass


class Beer(BeerBase):
    beer_id: int

    class Config:
        orm_mode = True


# User models
class UserBase(BaseModel):
    name: str
    email: str
    address: str | None
    phone: str | None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    user_id: int

    class Config:
        orm_mode = True


# Order models
class OrderBase(BaseModel):
    beer_id: int
    user_id: int
    qty: int
    ordered_at: datetime
    price: float


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    order_id: int

    class Config:
        orm_mode = True


# Stock models
class StockBase(BaseModel):
    beer_id: int
    qty_in_stock: int
    date_of_arrival: date


class StockCreate(StockBase):
    pass


class Stock(StockBase):
    stock_id: int

    class Config:
        orm_mode = True
