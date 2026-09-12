import hashlib
import hmac
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.db import get_auth_session
from creatorops.core.errors import ForbiddenError, UnauthorizedError
from creatorops.models.enums import BrandRole, UserKind
from creatorops.models.identity import BrandMembership, User

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: uuid.UUID
    kind: UserKind
    brand_id: uuid.UUID | None
    role: BrandRole | None


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(
    user: User,
    *,
    brand_id: uuid.UUID | None = None,
    role: BrandRole | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": str(user.id),
        "kind": user.kind.value,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    if brand_id:
        payload["brand_id"] = str(brand_id)
    if role:
        payload["role"] = role.value
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc


async def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_auth_session),
) -> Principal:
    if credentials is None:
        raise UnauthorizedError("Bearer token required")
    claims = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(str(claims["sub"]))
        kind = UserKind(str(claims["kind"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedError("Malformed token") from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.kind != kind:
        raise UnauthorizedError("User is inactive or missing")

    if kind == UserKind.CREATOR:
        return Principal(user_id=user.id, kind=kind, brand_id=None, role=None)

    try:
        brand_id = uuid.UUID(str(claims["brand_id"]))
        role = BrandRole(str(claims["role"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise UnauthorizedError("Staff token has no active brand") from exc

    membership = await session.scalar(
        select(BrandMembership).where(
            BrandMembership.user_id == user.id,
            BrandMembership.brand_id == brand_id,
            BrandMembership.role == role,
        )
    )
    if membership is None:
        raise UnauthorizedError("Brand membership no longer grants this role")
    return Principal(user_id=user.id, kind=kind, brand_id=brand_id, role=role)


async def require_creator(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.kind != UserKind.CREATOR:
        raise ForbiddenError(detail="Creator access required")
    return principal


def require_roles(*allowed: BrandRole) -> Callable[..., Awaitable[Principal]]:
    async def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.kind != UserKind.STAFF or principal.role not in allowed:
            raise ForbiddenError(detail=f"One of these roles is required: {', '.join(allowed)}")
        if principal.brand_id is None:
            raise ForbiddenError(detail="An active brand is required")
        return principal

    return dependency


def verify_hmac_signature(raw_body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(
        settings.commerce_webhook_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    supplied = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, supplied)


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
