import asyncpg
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from functools import lru_cache
from dotenv import load_dotenv
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
import structlog
import traceback

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Set up logging
logger = logging.getLogger(__name__)

# Get structured logger for database connections
logger = structlog.get_logger("shared.database.connection")

class DatabaseConnection:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.database_url = None
        logger.info("🔧 DatabaseConnection initialized")

    async def connect(self, database_url: str):
        """Connect to database with comprehensive logging"""
        self.database_url = database_url
        
        # Mask password in URL for logging
        safe_url = database_url
        if '@' in database_url:
            parts = database_url.split('@')
            if len(parts) > 1:
                # Keep only the part after @
                safe_url = f"***@{parts[-1]}"
        
        logger.info("📊 Attempting database connection", 
                   database_url=safe_url,
                   connection_type="async postgresql")
        
        try:
            # Create engine with connection pooling
            self.engine = create_async_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL query logging
            )
            
            logger.info("🛠️ Database engine created", 
                       pool_size=5,
                       max_overflow=10,
                       pool_pre_ping=True,
                       pool_recycle=3600)
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("🏭 Session factory created")
            
            # Test connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                test_result = result.scalar()
                
                logger.info("✅ Database connection test successful", 
                           test_query_result=test_result)
            
            # Test session creation
            async with self.session_factory() as session:
                result = await session.execute(text("SELECT current_database(), current_user, version()"))
                db_info = result.first()
                
                logger.info("✅ Database session test successful", 
                           current_database=db_info[0] if db_info else "unknown",
                           current_user=db_info[1] if db_info else "unknown",
                           postgresql_version=db_info[2][:50] if db_info and db_info[2] else "unknown")
                
                # Check for schema
                schema_result = await session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name IN ('profiles', 'referrals', 'insurance', 'notifications')
                    ORDER BY schema_name
                """))
                schemas = [row[0] for row in schema_result.fetchall()]
                
                logger.info("📋 Available schemas", 
                           schemas=schemas,
                           schema_count=len(schemas))
            
            logger.info("✅ Database connection established successfully", 
                       database_url=safe_url)
            
        except Exception as e:
            logger.error("❌ Database connection failed", 
                        database_url=safe_url,
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())
            raise

    async def disconnect(self):
        """Disconnect from database with logging"""
        logger.info("🔌 Disconnecting from database")
        
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("✅ Database engine disposed successfully")
            
            self.engine = None
            self.session_factory = None
            self.database_url = None
            
            logger.info("✅ Database disconnected successfully")
            
        except Exception as e:
            logger.error("❌ Database disconnect failed", 
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    async def get_session(self) -> AsyncSession:
        """Get database session with logging"""
        if not self.session_factory:
            logger.error("❌ Session factory not initialized")
            raise RuntimeError("Database connection not established")
        
        try:
            session = self.session_factory()
            logger.info("🔄 Database session created", 
                       session_id=id(session))
            return session
            
        except Exception as e:
            logger.error("❌ Failed to create database session", 
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    async def execute_raw_query(self, query: str, params: dict = None) -> any:
        """Execute raw SQL query with detailed logging"""
        logger.info("📝 Executing raw SQL query", 
                   query=query[:100] + "..." if len(query) > 100 else query,
                   params=params)
        
        try:
            async with self.session_factory() as session:
                if params:
                    result = await session.execute(text(query), params)
                else:
                    result = await session.execute(text(query))
                
                # Try to get results
                if result.returns_rows:
                    rows = result.fetchall()
                    logger.info("✅ Raw query executed successfully", 
                               row_count=len(rows),
                               has_results=True)
                    return rows
                else:
                    logger.info("✅ Raw query executed successfully", 
                               has_results=False)
                    return result.rowcount
                    
        except Exception as e:
            logger.error("❌ Raw query execution failed", 
                        query=query[:100] + "..." if len(query) > 100 else query,
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    async def check_connection(self) -> bool:
        """Check if database connection is healthy"""
        try:
            if not self.engine:
                logger.warning("⚠️ Database engine not initialized")
                return False
            
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection check successful")
                return True
                
        except Exception as e:
            logger.error("❌ Database connection check failed", 
                        error=str(e),
                        error_type=type(e).__name__)
            return False

# Global database connection instance
db = DatabaseConnection()

@lru_cache()
def get_database_url() -> str:
    """Get database URL from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return database_url

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions"""
    if not db.session_factory:
        raise RuntimeError("Database connection not established")
    
    async with db.session_factory() as session:
        logger.info("🔄 FastAPI dependency session created", session_id=id(session))
        try:
            yield session
        finally:
            logger.info("🔄 FastAPI dependency session closed", session_id=id(session))

# Alias for convenience
get_db_session = get_session