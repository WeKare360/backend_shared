from pydantic import  Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from shared.app.domain.entities.base import BaseEntity

class User(BaseEntity):
    cognito_user_id: str  # Cognito UUID (sub claim)
    cognito_username: str  # Usually email
    preferences: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "UTC"
    locale: str = "en"
    profile_settings: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    last_login_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
