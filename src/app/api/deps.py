import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
import jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "inventory:read": "Read inventory balances and paths",
        "inventory:write": "Execute stock moves and balance mutations",
        "po:read": "View purchase orders",
        "po:write": "Create and update purchase orders",
        "admin": "Root level access to administrative features",
    },
)


class CurrentUser(BaseModel):
    id: uuid.UUID
    scopes: list[str]


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = decode_access_token(token)
        user_id_raw: str = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        if user_id_raw is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_raw)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this resource",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return CurrentUser(id=user_id, scopes=token_scopes)


DBSession = Annotated[AsyncSession, Depends(get_db)]
