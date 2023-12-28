from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# Stock models
class StockBase(BaseModel):
    beer_id: int
    qty_in_stock: int
    date_of_arrival: date


class StockCreate(StockBase):
    pass


class Stock(StockBase):
    stock_id: int

    model_config = ConfigDict(from_attributes=True)


# Migration models
class MigrationBase(BaseModel):
    migration_filename: str


class Migration(MigrationBase):
    migration_id: int
    date_of_migration: datetime

    model_config = ConfigDict(from_attributes=True)
