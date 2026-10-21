from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import Base, build_engine, session_factory
from app.routes import academics, auth, reports, students
from app.services.prediction import load_model


def create_app(settings=None):
    @asynccontextmanager
    async def lifespan(app):
        config = settings or get_settings()
        engine = build_engine(config.database_url)
        app.state.settings = config
        app.state.sessions = session_factory(engine)
        try:
            # Initial schema bootstrap. Existing tables are never dropped or rewritten.
            Base.metadata.create_all(engine)
            app.state.model = load_model(config.model_path)
            yield
        finally:
            engine.dispose()

    api = FastAPI(
        title="Student Academic Performance API",
        version="1.0.0",
        lifespan=lifespan,
        description="Account-isolated academic records, analytics, and educational ML predictions.",
    )
    for router in (auth.router, students.router, academics.router, reports.router):
        api.include_router(router)

    @api.get("/", tags=["Status"])
    def home():
        return {"message": "Student Academic Performance API", "docs": "/docs", "version": "1.0.0"}

    @api.get("/health", tags=["Status"])
    def health(request: Request):
        try:
            with request.app.state.sessions() as db:
                db.execute(text("SELECT 1"))
        except SQLAlchemyError:
            raise HTTPException(503, "Database unavailable")
        return {"status": "healthy", "model_ready": request.app.state.model is not None}

    return api


app = create_app()
