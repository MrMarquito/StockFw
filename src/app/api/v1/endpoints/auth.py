import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Demonstration authentication verification logic
    if form_data.username == "warehouse_manager" and form_data.password == "SecretPass123!":
        user_id = uuid.UUID("a0000000-0000-0000-0000-000000000001")
        scopes = ["inventory:read", "inventory:write", "po:read", "po:write", "admin"]
    elif form_data.username == "floor_worker" and form_data.password == "FloorWorker123!":
        user_id = uuid.UUID("b0000000-0000-0000-0000-000000000002")
        scopes = ["inventory:read", "inventory:write"]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user_id, scopes=scopes)
    return TokenResponse(access_token=access_token, token_type="bearer")
