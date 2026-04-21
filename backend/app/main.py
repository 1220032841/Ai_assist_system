from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings

from app.api.v1.api import api_router
from app.db.session import engine

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

cors_origins = settings.get_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def ensure_schema_compatibility() -> None:
    # Keep old databases compatible with new teacher student-management features.
    async with engine.begin() as conn:
        users_table = await conn.execute(text("SELECT to_regclass('public.users')"))
        if users_table.scalar():
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS class_name VARCHAR"))
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS class_groups (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
                """
            )
        )
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_class_groups_id ON class_groups (id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_class_groups_name ON class_groups (name)"))

@app.get("/")
async def root():
    return {"message": "Welcome to AI-Assisted Teaching System API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
