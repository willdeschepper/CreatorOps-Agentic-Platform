from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal
from creatorops.schemas import (
    CreatorRegistrationResponse,
    MeResponse,
    RegisterCreatorRequest,
    SocialProfileResponse,
    TokenRequest,
    TokenResponse,
)
from creatorops.services import identity

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=CreatorRegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    body: RegisterCreatorRequest,
    session: AsyncSession = Depends(get_session),
) -> CreatorRegistrationResponse:
    user = await identity.register_creator(session, body)
    return CreatorRegistrationResponse.model_validate(user)


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
    user, context, socials = await identity.get_me(session, principal)
    return MeResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        kind=user.kind,
        brand_id=context.brand_id,
        role=context.role,
        socials=[SocialProfileResponse.model_validate(row) for row in socials],
    )
