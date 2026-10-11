"""Database models.

Every table module is imported here on purpose.

SQLModel registers a table on `SQLModel.metadata` only when its module is
imported, and both `init_db()` (app/database.py) and migrations/env.py use
that metadata as a whole. This module used to re-export only `User`, so a
process that imported `app.models` without separately importing
`app.models.opportunity` & co. would silently create, upgrade and
autogenerate against ONE of six tables.
"""

from app.models.api_key import ApiKey as ApiKey
from app.models.opportunity import Opportunity as Opportunity
from app.models.opportunity import OpportunityStatus as OpportunityStatus
from app.models.opportunity_change_log import (
    OpportunityChangeLog as OpportunityChangeLog,
)
from app.models.opportunity_update import OpportunityUpdate as OpportunityUpdate
from app.models.refresh_token import RefreshToken as RefreshToken
from app.models.user import User as User

__all__ = [
    "ApiKey",
    "Opportunity",
    "OpportunityChangeLog",
    "OpportunityStatus",
    "OpportunityUpdate",
    "RefreshToken",
    "User",
]
