import os

BEER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
ORDERS_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
STOCK_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
USER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))

DATABASE = "beerpy"
PGHOST = "localhost"
PORT = "5432"
USER = "aviv"
PASSWORD = "AsPsql23"
