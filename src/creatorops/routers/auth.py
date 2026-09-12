from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal
from creatorops.schemas import MeResponse, RegisterCreatorRequest, TokenRequest, TokenResponse
from creatorops.services import identity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterCreatorRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    user = await identity.register_creator(session, body)
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "kind": user.kind,
    }


@router.post("/token", response_model=TokenResponse)
async def token(
    body: TokenRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    return await identity.authenticate(session, body)


@router.get("/me", response_model=MeResponse)
async def me(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> MeResponse:
    user, context = await identity.get_me(session, principal)
    return MeResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        kind=user.kind,
        brand_id=context.brand_id,
        role=context.role,
    )
