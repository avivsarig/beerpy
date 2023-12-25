import os
import logging

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend import models, schemas, settings

from backend.database import get_db
from backend.migrator.migrator_utils import apply_state, list_available_migrations

from backend.utils.error_handler import response_from_error

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter(prefix="/v1/migrator")
MIGRATION_FOLDER = os.getenv("MIGRATION_FOLDER", settings.MIGRATION_FOLDER)


@router.get(
    "/",
    response_model=list[schemas.Migration],
    summary="List All Migrations",
    description="Fetch and return a list of all applied migrations from the database.",
)
async def get_migrations(db: Session = Depends(get_db)):
    logging.info("Fetching all migrations from the database...")
    try:
        query = db.query(models.Migration)
        migrations = query.all()

        logging.info(f"Fetched {len(migrations)} migrations.")
        return migrations

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)


@router.get(
    "/state",
    response_model=schemas.Migration,
    summary="Get Latest Migration State",
    description="Retrieve the latest migration that was applied to the database.",
)
async def get_db_state(db: Session = Depends(get_db)):
    try:
        last_migration = (
            db.query(models.Migration)
            .order_by(models.Migration.date_of_migration.desc())
            .first()
        )
        if last_migration is None:
            logging.warning("No migrations found in the database.")
            raise HTTPException(status_code=404, detail="No migrations found\n")

        return last_migration

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)


@router.post(
    "/init",
    summary="Initialize Database",
    description="Run the initial migration script to set up the database for the first time.",
)
async def initialize_database(db: Session = Depends(get_db)) -> dict:
    try:
        logging.info("Initializing Database")

        await apply_state(MIGRATION_FOLDER + "0001_init_db.sql", db)
        return {"detail": "Database initialized successfully!"}

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)


@router.post(
    "/migrate",
    status_code=201,
    response_model=schemas.Migration,
    summary="Apply Pending Migrations",
    description="Identify and apply all migrations that are pending since the last applied migration.",
)
async def migrate(db: Session = Depends(get_db)):
    try:
        db_state = await get_db_state(db)
        db_state_filename = getattr(db_state, "migration_filename")

        available_migrations = list_available_migrations()
        pending_migrations = available_migrations[
            available_migrations.index(MIGRATION_FOLDER + db_state_filename) + 1 :
        ]
        logging.info(f"Found {len(pending_migrations)} pending migrations.")

        for migration_file in pending_migrations:
            # Validate before migration the proper sequence is kept
            db_state = await get_db_state(db)
            state_id = int(getattr(db_state, "migration_id"))
            migration_id = int(migration_file.replace(MIGRATION_FOLDER, "")[0:4]) + 1

            if migration_id - state_id != 1:
                raise HTTPException(
                    status_code=400, detail="Out of order migration detected."
                )

            await apply_state(migration_file, db)

            # Validate sucessful application
            new_db_state = await get_db_state(db)
            state_id = int(getattr(new_db_state, "migration_id"))

            if state_id != migration_id:
                raise HTTPException(
                    status_code=500, detail="Migration did not apply as expected."
                )

        return await get_db_state(db)

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)


# TODO: add rollback
