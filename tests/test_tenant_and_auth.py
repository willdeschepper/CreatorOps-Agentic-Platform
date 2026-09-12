from httpx import AsyncClient

from creatorops.models.enums import BrandRole
from tests.helpers import auth, create_domain_fixture


async def test_health_authentication_and_tenant_isolation(client: AsyncClient) -> None:
    tenant_a = await create_domain_fixture(role=BrandRole.OWNER, creator_count=0)
    tenant_b = await create_domain_fixture(role=BrandRole.OWNER, creator_count=0)

    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"

    token = await client.post(
        "/v1/auth/token",
        json={
            "email": tenant_a.staff_email,
            "password": "CreatorOps123!",
            "brand_slug": tenant_a.brand_slug,
        },
    )
    assert token.status_code == 200
    assert token.json()["token_type"] == "bearer"

    cross_tenant = await client.post(
        f"/v1/programs/{tenant_b.program_id}/status",
        headers=auth(tenant_a.staff_token),
        json={"status": "paused"},
    )
    assert cross_tenant.status_code == 404
    assert cross_tenant.json()["code"] == "program_not_found"
