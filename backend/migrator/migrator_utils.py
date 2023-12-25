import os
import glob
import logging

from fastapi import Depends, HTTPException

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend import settings
from backend.database import get_db
from backend.utils.error_handler import response_from_error

MIGRATION_FOLDER = os.getenv("MIGRATION_FOLDER", settings.MIGRATION_FOLDER)


async def apply_state(filepath: str, db: Session = Depends(get_db)):
    try:
        logging.info(f"Reading migration file: {filepath}")
        with open(f"{filepath}", "r") as file:
            init_script = file.read()
            db.execute(text(init_script))
            db.commit()
            logging.info(f"Successfully applied migration from {filepath}")

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)


def list_available_migrations() -> list:
    try:
        pattern = f"{MIGRATION_FOLDER}*.sql"
        available_migrations = glob.glob(pattern)

        available_migrations.sort(
            key=lambda filename: int(filename.replace(MIGRATION_FOLDER, "")[:4])
        )

        if len(available_migrations) == 0:
            logging.warning("No migration files found in the migration folder.")
            raise HTTPException(status_code=404, detail="No migration files found\n")

        return available_migrations

    except IntegrityError as e:
        code, message = response_from_error(e)
        logging.error(f"IntegrityError occurred with code {code}. Message: {message}")
        raise HTTPException(status_code=code, detail=message)
