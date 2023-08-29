DO $$ 
DECLARE
   table_name_var text;
BEGIN
   FOR table_name_var IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
   LOOP
      EXECUTE 'DROP TABLE IF EXISTS ' || table_name_var || ' CASCADE';
   END LOOP;
END $$;

CREATE TABLE beers (
    beer_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    style VARCHAR NOT NULL,
    abv FLOAT,
    price FLOAT
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    address VARCHAR,
    phone VARCHAR
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    beer_id INTEGER REFERENCES beers(beer_id) UNIQUE,
    user_id INTEGER REFERENCES users(user_id) UNIQUE,
    qty INTEGER NOT NULL,
    ordered_at TIMESTAMP WITHOUT TIME ZONE,
    price FLOAT
);

CREATE TABLE stock (
    stock_id SERIAL PRIMARY KEY,
    beer_id INTEGER REFERENCES beers(beer_id) UNIQUE,
    qty_in_stock INTEGER NOT NULL,
    date_of_arrival TIMESTAMP WITHOUT TIME ZONE
);

CREATE TABLE migrations (
    migration_id SERIAL PRIMARY KEY,
    migration_filename VARCHAR NOT NULL,
    date_of_migration TIMESTAMP WITHOUT TIME ZONE default CURRENT_TIMESTAMP
);

INSERT INTO migrations (migration_filename, date_of_migration)
VALUES ('0001_init_db.sql', NOW());