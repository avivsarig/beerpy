import os

BEER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
ORDERS_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
STOCK_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
USER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))

MIGRATION_FOLDER = os.getenv("MIGRATION_FOLDER", "./backend/migrator/migrations/")

DATABASE = os.getenv("DATABASE", "beerpy")
PGHOST = os.getenv("PGHOST", "localhost")
PORT = os.getenv("PORT", "5432")
DB_USER = os.getenv("DB_USER", "aviv")
PASSWORD = os.getenv("BEERPY_PASSWORD", "")
