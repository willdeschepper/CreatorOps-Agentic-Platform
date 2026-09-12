import asyncio

from sqlalchemy import select

from creatorops.core.db import session_factory
from creatorops.core.security import hash_password
from creatorops.models.enums import BrandRole, UserKind
from creatorops.models.identity import Brand, BrandMembership, User

DEMO_BRAND_SLUG = "creatorops-demo"
DEMO_PASSWORD = "CreatorOps123!"
STAFF_USERS = (
    ("owner@creatorops.dev", "Olivia Owner", BrandRole.OWNER),
    ("ops@creatorops.dev", "Oscar Ops", BrandRole.OPS),
    ("finance@creatorops.dev", "Fernanda Finance", BrandRole.FINANCE),
)


async def seed_database() -> dict[str, object]:
    async with session_factory() as session, session.begin():
        brand = await session.scalar(select(Brand).where(Brand.slug == DEMO_BRAND_SLUG))
        if brand is None:
            brand = Brand(name="CreatorOps Demo Brand", slug=DEMO_BRAND_SLUG)
            session.add(brand)
            await session.flush()

        users: list[str] = []
        for email, display_name, role in STAFF_USERS:
            user = await session.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(
                    email=email,
                    password_hash=hash_password(DEMO_PASSWORD),
                    display_name=display_name,
                    kind=UserKind.STAFF,
                )
                session.add(user)
                await session.flush()
            membership = await session.scalar(
                select(BrandMembership).where(
                    BrandMembership.brand_id == brand.id,
                    BrandMembership.user_id == user.id,
                )
            )
            if membership is None:
                session.add(BrandMembership(brand_id=brand.id, user_id=user.id, role=role))
            users.append(email)
    return {
        "brand_slug": DEMO_BRAND_SLUG,
        "password": DEMO_PASSWORD,
        "staff_users": users,
    }


def run() -> None:
    result = asyncio.run(seed_database())
    print("CreatorOps local seed is ready:")
    print(result)


if __name__ == "__main__":
    run()
