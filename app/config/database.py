from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy import event, text
from app.config.settings import settings
from app.config.logging import db_logger, app_logger
from app.models.base import Base
from app.handlers.exceptions import SchemaNotFoundError, DatabaseConnectionError

# Create async engine for Neon PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,       # Check connection before using
    pool_size=10,             # Connection pool size
    max_overflow=20,          # Extra connections allowed
)

# Event listener to set schema on each connection
@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set the schema for all database operations"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET search_path TO {settings.DB_SCHEMA}, public")
        cursor.close()
        db_logger.debug(f"Schema search_path set to {settings.DB_SCHEMA}")
    except Exception as e:
        db_logger.error(f"Failed to set schema search_path: {str(e)}")
        raise DatabaseConnectionError(
            f"Failed to set schema search_path: {str(e)}",
            details={"schema": settings.DB_SCHEMA}
        )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Function to initialize database schema and create tables
async def init_db():
    """
    Verify schema exists and create all tables.
    
    Raises:
        SchemaNotFoundError: If the schema does not exist
        DatabaseConnectionError: If unable to connect to database
    """
    try:
        async with engine.begin() as conn:
            # Check if schema exists
            result = await conn.execute(
                text(
                    f"SELECT schema_name FROM information_schema.schemata "
                    f"WHERE schema_name = '{settings.DB_SCHEMA}'"
                )
            )
            schema_exists = result.scalar() is not None
            
            if not schema_exists:
                db_logger.error(
                    f"Database schema '{settings.DB_SCHEMA}' does not exist",
                    extra={"schema": settings.DB_SCHEMA}
                )
                raise SchemaNotFoundError(settings.DB_SCHEMA)
            
            db_logger.info(f"Schema '{settings.DB_SCHEMA}' verified successfully")
            
            # Create all tables in the schema
            # Note: schema is already defined in models via __table_args__ = {'schema': settings.DB_SCHEMA}
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(sync_conn)
            )
            db_logger.info(f"Database tables created in schema '{settings.DB_SCHEMA}'")
            app_logger.info("Database initialization completed successfully")
            
    except SchemaNotFoundError:
        raise
    except Exception as e:
        db_logger.error(
            f"Database initialization failed: {str(e)}",
            exc_info=True,
            extra={"schema": settings.DB_SCHEMA}
        )
        raise DatabaseConnectionError(
            f"Failed to initialize database: {str(e)}",
            details={"schema": settings.DB_SCHEMA}
        )

# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for FastAPI dependency injection.
    
    Yields:
        AsyncSession: Database session
        
    Raises:
        DatabaseConnectionError: If session creation fails
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
            db_logger.debug("Database transaction committed")
        except Exception as e:
            await session.rollback()
            db_logger.error(
                f"Database transaction rollback: {str(e)}",
                exc_info=True
            )
            raise DatabaseConnectionError(
                f"Database operation failed: {str(e)}"
            )
        finally:
            await session.close()
            db_logger.debug("Database session closed")