from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.errors import ConflictError, NotFoundError, UnauthorizedError
from creatorops.core.security import (
    Principal,
    create_access_token,
    hash_password,
    verify_password,
)
from creatorops.models.enums import UserKind
from creatorops.models.identity import Brand, BrandMembership, SocialProfile, User
from creatorops.schemas import RegisterCreatorRequest, TokenRequest, TokenResponse
from creatorops.services.shared import normalize_email, normalize_handle


async def register_creator(session: AsyncSession, request: RegisterCreatorRequest) -> User:
    email = normalize_email(str(request.email))
    user = User(
        email=email,
        password_hash=hash_password(request.password),
        display_name=request.display_name.strip(),
        kind=UserKind.CREATOR,
    )
    try:
        async with session.begin():
            session.add(user)
            await session.flush()
            for social in request.socials:
                session.add(
                    SocialProfile(
                        creator_id=user.id,
                        network=social.network,
                        handle=social.handle.strip(),
                        handle_normalized=normalize_handle(social.handle),
                        verified=True,
                    )
                )
    except IntegrityError as exc:
        raise ConflictError(
            "creator_already_exists",
            "The email or social handle is already registered",
        ) from exc
    return user


async def authenticate(session: AsyncSession, request: TokenRequest) -> TokenResponse:
    email = normalize_email(str(request.email))
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise UnauthorizedError()
    if not user.is_active:
        raise UnauthorizedError("User is inactive")

    if user.kind == UserKind.CREATOR:
        token = create_access_token(user)
    else:
        if request.brand_slug is None:
            raise UnauthorizedError("Staff login requires brand_slug")
        row = (
            await session.execute(
                select(BrandMembership, Brand)
                .join(Brand, Brand.id == BrandMembership.brand_id)
                .where(
                    BrandMembership.user_id == user.id,
                    Brand.slug == request.brand_slug,
                )
            )
        ).first()
        if row is None:
            raise UnauthorizedError("User does not belong to this brand")
        membership, brand = row
        token = create_access_token(
            user,
            brand_id=brand.id,
            role=membership.role,
        )
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_minutes * 60,
    )


async def get_me(session: AsyncSession, principal: Principal) -> tuple[User, Principal]:
    user = await session.get(User, principal.user_id)
    if user is None:
        raise NotFoundError("user_not_found", "User no longer exists")
    return user, principal
