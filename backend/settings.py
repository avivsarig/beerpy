import os

BEER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
ORDERS_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
STOCK_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))
USER_PAGE_LIMIT = int(os.getenv("BEER_PAGE_LIMIT", "20"))

DATABASE = os.getenv("DATABASE", "beerpy")
PGHOST = os.getenv("PGHOST", "localhost")
PORT = os.getenv("PORT", "5432")
DB_USER = os.getenv("DB_USER", "aviv")
PASSWORD = os.getenv("BEERPY_PASSWORD", "")

TEST_DATABASE = os.getenv("TEST_DATABASE", "test_beerpy")
TEST_PGHOST = os.getenv("TEST_PGHOST", "localhost")
TEST_PORT = os.getenv("TEST_PORT", "5432")
TEST_USER = os.getenv("TEST_USER", "test_user")
TEST_PASSWORD = os.getenv("TEST_BEERPY_PASSWORD", "")
