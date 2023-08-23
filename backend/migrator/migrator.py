from fastapi import APIRouter, Depends, HTTPException, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.migrator.test_db import get_db
from backend import models, schemas, settings

from backend.utils.error_handler import response_from_error

router = APIRouter(prefix="/migrator")


@router.get("/last", response_model=list[schemas.Migration])
async def get_last_migration(db: Session = Depends(get_db)):
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
