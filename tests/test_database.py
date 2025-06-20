"""
Tests for Database modules
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

# Import the modules to test
from shared.database.connection import (
    DatabaseConnection, 
    db, 
    get_database_url, 
    get_session
)
from shared.database.base import Base, BaseTable, OrganizationMixin
from shared.database.repository import BaseRepository


class TestDatabaseConnection:
    """Test the DatabaseConnection class"""
    
    @pytest.fixture
    def db_connection(self):
        """Create a fresh DatabaseConnection instance for testing"""
        return DatabaseConnection()
    
    @pytest.mark.asyncio
    async def test_connection_initialization(self, db_connection):
        """Test DatabaseConnection initialization"""
        assert db_connection.engine is None
        assert db_connection.session_factory is None
        assert db_connection.database_url is None
    
    @pytest.mark.asyncio
    async def test_connect_success(self, db_connection):
        """Test successful database connection"""
        test_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        
        # Mock the engine and session creation
        with patch('shared.database.connection.create_async_engine') as mock_engine, \
             patch('shared.database.connection.async_sessionmaker') as mock_session_maker, \
             patch.object(db_connection, 'engine') as mock_engine_instance:
            
            # Mock successful connection test
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 1
            mock_conn.execute.return_value = mock_result
            mock_engine_instance.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine_instance.begin.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock session test
            mock_session = AsyncMock()
            mock_session_result = MagicMock()
            mock_session_result.first.return_value = ("test_db", "test_user", "PostgreSQL 13.0")
            mock_session_result.fetchall.return_value = [("profiles",), ("referrals",)]
            mock_session.execute.return_value = mock_session_result
            
            mock_session_factory = MagicMock()
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker.return_value = mock_session_factory
            
            await db_connection.connect(test_url)
            
            assert db_connection.database_url == test_url
            mock_engine.assert_called_once()
            mock_session_maker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, db_connection):
        """Test database connection failure"""
        test_url = "postgresql+asyncpg://invalid:invalid@nonexistent:5432/invalid_db"
        
        with patch('shared.database.connection.create_async_engine') as mock_engine:
            mock_engine.side_effect = SQLAlchemyError("Connection failed")
            
            with pytest.raises(SQLAlchemyError):
                await db_connection.connect(test_url)
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, db_connection):
        """Test successful database disconnection"""
        # Setup connection first
        mock_engine = AsyncMock()
        mock_engine.dispose = AsyncMock()
        db_connection.engine = mock_engine
        db_connection.session_factory = MagicMock()
        db_connection.database_url = "test_url"
        
        await db_connection.disconnect()
        
        mock_engine.dispose.assert_called_once()
        assert db_connection.engine is None
        assert db_connection.session_factory is None
        assert db_connection.database_url is None
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, db_connection):
        """Test successful session creation"""
        mock_session = AsyncMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        db_connection.session_factory = mock_session_factory
        
        session = await db_connection.get_session()
        
        assert session == mock_session
        mock_session_factory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_not_connected(self, db_connection):
        """Test session creation when not connected"""
        with pytest.raises(RuntimeError, match="Database connection not established"):
            await db_connection.get_session()
    
    @pytest.mark.asyncio
    async def test_check_connection_healthy(self, db_connection):
        """Test connection health check when healthy"""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()
        
        # Create proper async context manager
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_context_manager
        
        db_connection.engine = mock_engine
        
        result = await db_connection.check_connection()
        
        assert result is True
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_connection_unhealthy(self, db_connection):
        """Test connection health check when unhealthy"""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = SQLAlchemyError("Connection lost")
        mock_engine = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_connection.engine = mock_engine
        
        result = await db_connection.check_connection()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_connection_no_engine(self, db_connection):
        """Test connection health check when no engine"""
        result = await db_connection.check_connection()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_execute_raw_query_with_results(self, db_connection):
        """Test executing raw query that returns results"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.returns_rows = True
        mock_result.fetchall.return_value = [("row1",), ("row2",)]
        mock_session.execute.return_value = mock_result
        
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_connection.session_factory = mock_session_factory
        
        result = await db_connection.execute_raw_query("SELECT * FROM test_table")
        
        assert result == [("row1",), ("row2",)]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_raw_query_without_results(self, db_connection):
        """Test executing raw query that doesn't return results"""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.returns_rows = False
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_connection.session_factory = mock_session_factory
        
        result = await db_connection.execute_raw_query("UPDATE test_table SET column = 'value'")
        
        assert result == 1
        mock_session.execute.assert_called_once()


class TestGetDatabaseUrl:
    """Test the get_database_url function"""
    
    def test_get_database_url_success(self):
        """Test successful database URL retrieval"""
        test_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        
        with patch.dict('os.environ', {'DATABASE_URL': test_url}):
            url = get_database_url()
            assert url == test_url
    
    def test_get_database_url_missing(self):
        """Test database URL retrieval when environment variable is missing"""
        # Clear the cache first
        get_database_url.cache_clear()
        
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
                get_database_url()


class TestGetSession:
    """Test the get_session FastAPI dependency"""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test successful session creation through FastAPI dependency"""
        mock_session = AsyncMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch.object(db, 'session_factory', mock_session_factory):
            session_generator = get_session()
            session = await session_generator.__anext__()
            
            assert session == mock_session
    
    @pytest.mark.asyncio
    async def test_get_session_not_established(self):
        """Test session creation when connection not established"""
        with patch.object(db, 'session_factory', None):
            with pytest.raises(RuntimeError, match="Database connection not established"):
                session_generator = get_session()
                await session_generator.__anext__()


class TestBaseModels:
    """Test the base database models"""
    
    def test_base_table_mixin(self):
        """Test BaseTable mixin provides required fields"""
        # Create a test model using BaseTable
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
        
        class TestBase(DeclarativeBase):
            pass
        
        class TestModel(BaseTable, TestBase):
            __tablename__ = 'test_model'
        
        # Check that BaseTable fields are present
        assert hasattr(TestModel, 'id')
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')
        
        # Verify field types
        assert hasattr(TestModel.id, 'type')
        assert hasattr(TestModel.created_at, 'type')
        assert hasattr(TestModel.updated_at, 'type')
    
    def test_organization_mixin(self):
        """Test OrganizationMixin provides organization_id field"""
        from sqlalchemy.orm import DeclarativeBase
        
        class TestBase(DeclarativeBase):
            pass
        
        # Combine with BaseTable to get required primary key
        class TestModel(BaseTable, OrganizationMixin, TestBase):
            __tablename__ = 'test_org_model'
        
        # Check that OrganizationMixin field is present
        assert hasattr(TestModel, 'organization_id')
        
        # Verify field properties
        assert hasattr(TestModel.organization_id, 'type')
    
    def test_combined_mixins(self):
        """Test using both BaseTable and OrganizationMixin together"""
        from sqlalchemy.orm import DeclarativeBase
        
        class TestBase(DeclarativeBase):
            pass
        
        class TestModel(BaseTable, OrganizationMixin, TestBase):
            __tablename__ = 'test_combined_model'
        
        # Check all fields are present
        assert hasattr(TestModel, 'id')
        assert hasattr(TestModel, 'created_at')
        assert hasattr(TestModel, 'updated_at')
        assert hasattr(TestModel, 'organization_id')


# Note: BaseRepository tests have been consolidated in test_repository.py to avoid duplication