import os

BEER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
ORDERS_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
STOCK_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
USER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))

DATABASE = os.getenv("DATABASE", "beerpy")
PGHOST = os.getenv("PGHOST", "localhost")
PORT =  os.getenv("PORT", "5432")
USER = os.getenv("USER", "aviv")
PASSWORD = os.getenv("PASSWORD", "AsPsql23")
