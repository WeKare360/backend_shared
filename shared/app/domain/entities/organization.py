from pydantic import  Field
from typing import Optional, Dict, Any, List

from shared.app.domain.entities.base import BaseEntity


class Organization(BaseEntity):
    name: str
    slug: str
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_domain_prefix: Optional[str] = None
    region: str = "us-east-1"
    settings: Dict[str, Any] = Field(default_factory=dict)
    subscription_plan: str = "free"