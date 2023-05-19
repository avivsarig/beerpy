from peewee import *
import json

config = json.load(open("./backend/config.json", "r"))

db = PostgresqlDatabase(None)

db_name = config["DATABASE"]
db_host = config["PGHOST"]
db_user = config["USER"]
db_password = config["PASSWORD"]

db.init(db_name, host=db_host, user=db_user, password=db_password)
