from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from uuid import UUID

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class
    
    async def create(self, **kwargs) -> T:
        """Create new record"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get record by ID"""
        stmt = select(self.model_class).where(getattr(self.model_class, "id") == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None, 
                     order_by: Optional[str] = None) -> List[T]:
        """Get all records with optional pagination and ordering"""
        stmt = select(self.model_class)
        
        # Add ordering if specified
        if order_by and hasattr(self.model_class, order_by):
            order_column = getattr(self.model_class, order_by)
            stmt = stmt.order_by(order_column)
        elif hasattr(self.model_class, 'created_at'):
            # Default ordering by created_at if available
            stmt = stmt.order_by(getattr(self.model_class, 'created_at').desc())
        
        # Add pagination if specified
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_organization(self, organization_id: UUID) -> List[T]:
        """Get records by organization (for multi-tenant models)"""
        if hasattr(self.model_class, 'organization_id'):
            stmt = select(self.model_class).where(
                getattr(self.model_class, 'organization_id', None) == organization_id
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        raise AttributeError(f"{self.model_class.__name__} is not multi-tenant")
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update record"""
        stmt = update(self.model_class).where(
            getattr(self.model_class, "id") == id
        ).values(**kwargs).returning(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete(self, id: UUID) -> bool:
        """Delete record"""
        stmt = delete(self.model_class).where(getattr(self.model_class, "id") == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def count(self) -> int:
        """Get total count of records"""
        from sqlalchemy import func
        stmt = select(func.count(getattr(self.model_class, 'id')))
        result = await self.session.execute(stmt)
        return result.scalar_one()