from fastapi import FastAPI
from . import database, models
from .auth_router import router as auth_router
import os

app = FastAPI(title="SignBridge Auth API")

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    # ensure database directory exists
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    # create tables
    models.Base = database.Base if not hasattr(models, 'Base') else models.Base
    database.Base.metadata.create_all(bind=database.engine)


@app.get('/')
def root():
    return {"message": "SignBridge Auth API"}
