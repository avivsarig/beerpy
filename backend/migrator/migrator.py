import os, glob
import pysnooper

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.migrator.test_db import get_db
from backend import models, schemas, settings

from backend.utils.error_handler import response_from_error


router = APIRouter(prefix="/migrate")
MIGRATION_FOLDER = os.getenv("MIGRATION_FOLDER", settings.MIGRATION_FOLDER)


@router.post("/initialize")
async def initialize_database(db: Session = Depends(get_db)):
    try:
        apply_state(1, db)
        return {"detail": "Database initialized successfully!"}

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.get("/state", response_model=schemas.Migration)
async def get_db_state(db: Session = Depends(get_db)):
    try:
        last_migration = (
            db.query(models.Migration)
            .order_by(models.Migration.date_of_migration)
            .first()
        )
        if last_migration is None:
            raise HTTPException(status_code=404, detail="No migrations found\n")

        return last_migration

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


@router.post("/apply", response_model=list[schemas.Migration], status_code=201)
async def apply_migrations(
    migration=schemas.MigrationBase, db: Session = Depends(get_db)
):
    try:
        db_migration = models.Migration(**migration.dict())
        db_state = get_db_state(db)
        if db_migration.id >= db_state.id:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot apply {db_migration.migration_filename}\n",
            )
        # TODO:
        # fetch_pending_migrations(db_state.id, db)

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


async def apply_state(id, db: Session = Depends(get_db)):
    filepath = id_to_filepath(id)
    try:
        with open(f"{filepath}", "r") as file:
            init_script = file.read()
            db.execute(text(init_script))
            db.commit()

        filename = filepath.replace(MIGRATION_FOLDER, "")
        return {"detail": f"Database migrated to {filename}!"}

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


def id_to_filepath(id: int):
    id_str = str(id).rjust(4, "0")
    try:
        pattern = f"{MIGRATION_FOLDER}{id_str}_*.sql"
        migration_files = glob.glob(pattern)
        if len(migration_files) == 1:
            return migration_files[0]

        elif len(migration_files) < 1:
            raise HTTPException(status_code=404, detail="Migration file not found\n")

        elif len(migration_files) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multiple migration files with id={id_str} found\n",
            )

    except IntegrityError as e:
        code, message = response_from_error(e)
        raise HTTPException(status_code=code, detail=message)


# TODO: add rollback
