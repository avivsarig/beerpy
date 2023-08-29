import os, glob, datetime

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.migrator.test_db import get_db
from backend import models, schemas, settings

from backend.utils.error_handler import response_from_error


router = APIRouter(prefix="/migrate")
MIGRATION_FOLDER = os.getenv("MIGRATION_FOLDER", settings.MIGRATION_FOLDER)


@router.get("/", response_model=list[schemas.Migration])
async def get_migrations(db: Session = Depends(get_db)):
    try:
        query = db.query(models.Migration)
        migrations = query.all()
        return migrations

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.post("/init")
async def initialize_database(db: Session = Depends(get_db)):
    try:
        await apply_state(MIGRATION_FOLDER + "0001_init_db.sql", db)
        return {"detail": "Database initialized successfully!"}

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.get("/state", response_model=schemas.Migration)
async def get_db_state(db: Session = Depends(get_db)):
    try:
        last_migration = (
            db.query(models.Migration)
            .order_by(models.Migration.date_of_migration.desc())
            .first()
        )
        if last_migration is None:
            raise HTTPException(status_code=404, detail="No migrations found\n")

        return last_migration

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.post("/migrate", status_code=201)
async def migrate(db: Session = Depends(get_db)):
    try:
        db_state = await get_db_state(db)
        obj_to_dict_lambda = lambda obj: {
            c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs
        }
        db_state_dict = obj_to_dict_lambda(db_state)

        available_migrations = list_available_migrations()
        pending_migrations = available_migrations[
            available_migrations.index(
                MIGRATION_FOLDER + db_state_dict["migration_filename"]
            )
            + 1 :
        ]

        print("Migration to perform:")
        [print(f"{migration_file}") for migration_file in pending_migrations]
        print("\n")

        for migration_file in pending_migrations:
            res = await apply_state(migration_file, db)
            print(res)

        return await get_db_state(db)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def apply_state(filepath, db: Session = Depends(get_db)):
    try:
        with open(f"{filepath}", "r") as file:
            init_script = file.read()
            db.execute(text(init_script))
            db.commit()

        filename = filepath.replace(MIGRATION_FOLDER, "")
        return f"Database migrated to {filename}"

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


def list_available_migrations():
    try:
        pattern = f"{MIGRATION_FOLDER}*.sql"
        available_migrations = glob.glob(pattern)

        available_migrations.sort(
            key=lambda filename: int(filename.replace(MIGRATION_FOLDER, "")[:4])
        )

        if len(available_migrations) == 0:
            raise HTTPException(status_code=404, detail="No migration files found\n")

        return available_migrations

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


# TODO: add rollback
