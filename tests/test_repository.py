"""
Tests for Base Repository module
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.repository import BaseRepository


class TestBaseRepository:
    """Test the BaseRepository class"""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_model_class(self):
        """Create a mock model class"""
        model = MagicMock()
        model.__name__ = "TestModel"
        model.id = MagicMock()
        model.created_at = MagicMock()
        model.organization_id = MagicMock()
        return model
    
    @pytest.fixture
    def repository(self, mock_session, mock_model_class):
        """Create a BaseRepository instance"""
        return BaseRepository(mock_session, mock_model_class)
    
    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_session, mock_model_class):
        """Test successful record creation"""
        test_data = {"name": "Test Item", "description": "Test Description"}
        mock_instance = MagicMock()
        mock_model_class.return_value = mock_instance
        
        result = await repository.create(**test_data)
        
        # Verify model instance was created with correct data
        mock_model_class.assert_called_once_with(**test_data)
        
        # Verify session operations
        mock_session.add.assert_called_once_with(mock_instance)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_instance)
        
        assert result == mock_instance
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_get_by_id_found(self, mock_select, repository, mock_session, mock_model_class):
        """Test getting record by ID when found"""
        test_id = uuid4()
        mock_stmt = MagicMock()
        mock_select.return_value.where.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "found_record"
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_by_id(test_id)
        
        assert result == "found_record"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_get_by_id_not_found(self, mock_select, repository, mock_session, mock_model_class):
        """Test getting record by ID when not found"""
        test_id = uuid4()
        mock_stmt = MagicMock()
        mock_select.return_value.where.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_by_id(test_id)
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_get_all_basic(self, mock_select, repository, mock_session, mock_model_class):
        """Test getting all records without pagination"""
        mock_stmt = MagicMock()
        mock_select.return_value.order_by.return_value = mock_stmt
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["record1", "record2", "record3"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_all()
        
        assert result == ["record1", "record2", "record3"]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_get_all_with_pagination(self, mock_select, repository, mock_session, mock_model_class):
        """Test getting all records with pagination"""
        mock_stmt = MagicMock()
        mock_select.return_value.order_by.return_value.offset.return_value.limit.return_value = mock_stmt
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["record1", "record2"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_all(limit=2, offset=10)
        
        assert result == ["record1", "record2"]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_get_by_organization_success(self, mock_select, repository, mock_session, mock_model_class):
        """Test getting records by organization"""
        test_org_id = uuid4()
        mock_stmt = MagicMock()
        mock_select.return_value.where.return_value = mock_stmt
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["org_record1", "org_record2"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_by_organization(test_org_id)
        
        assert result == ["org_record1", "org_record2"]
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_organization_not_multitenant(self, repository, mock_session):
        """Test getting records by organization when model is not multi-tenant"""
        # Create a model without organization_id
        non_tenant_model = MagicMock()
        non_tenant_model.__name__ = "NonTenantModel"
        # Remove organization_id attribute
        if hasattr(non_tenant_model, 'organization_id'):
            delattr(non_tenant_model, 'organization_id')
        repository.model_class = non_tenant_model
        
        test_org_id = uuid4()
        
        with pytest.raises(AttributeError):
            await repository.get_by_organization(test_org_id)
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.update')
    async def test_update_success(self, mock_update, repository, mock_session, mock_model_class):
        """Test successful record update"""
        test_id = uuid4()
        test_data = {"name": "Updated Name"}
        mock_stmt = MagicMock()
        mock_update.return_value.where.return_value.values.return_value.returning.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "updated_record"
        mock_session.execute.return_value = mock_result
        
        result = await repository.update(test_id, **test_data)
        
        assert result == "updated_record"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.update')
    async def test_update_not_found(self, mock_update, repository, mock_session, mock_model_class):
        """Test updating non-existent record"""
        test_id = uuid4()
        test_data = {"name": "Updated Name"}
        mock_stmt = MagicMock()
        mock_update.return_value.where.return_value.values.return_value.returning.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.update(test_id, **test_data)
        
        assert result is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.delete')
    async def test_delete_success(self, mock_delete, repository, mock_session, mock_model_class):
        """Test successful record deletion"""
        test_id = uuid4()
        mock_stmt = MagicMock()
        mock_delete.return_value.where.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        result = await repository.delete(test_id)
        
        assert result is True
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.delete')
    async def test_delete_not_found(self, mock_delete, repository, mock_session, mock_model_class):
        """Test deleting non-existent record"""
        test_id = uuid4()
        mock_stmt = MagicMock()
        mock_delete.return_value.where.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await repository.delete(test_id)
        
        assert result is False
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('shared.database.repository.select')
    async def test_count(self, mock_select, repository, mock_session, mock_model_class):
        """Test counting records"""
        mock_stmt = MagicMock()
        mock_select.return_value = mock_stmt
        
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result
        
        result = await repository.count()
        
        assert result == 42
        mock_session.execute.assert_called_once()
    
    def test_repository_initialization(self, mock_session, mock_model_class):
        """Test repository initialization"""
        repo = BaseRepository(mock_session, mock_model_class)
        
        assert repo.session == mock_session
        assert repo.model_class == mock_model_class 