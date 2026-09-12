import asyncio
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from creatorops.core.config import settings
from creatorops.seed import DEMO_BRAND_SLUG, DEMO_PASSWORD, seed_database

API_URL = os.getenv("CREATOROPS_API_URL", "http://localhost:8000").rstrip("/")


class DemoFailure(RuntimeError):
    pass


async def _request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    token: str | None = None,
    json_body: dict[str, Any] | None = None,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    merged = dict(headers or {})
    if token:
        merged["Authorization"] = f"Bearer {token}"
    response = await client.request(
        method,
        path,
        json=json_body,
        content=content,
        headers=merged,
    )
    if response.status_code >= 400:
        raise DemoFailure(f"{method} {path} failed ({response.status_code}): {response.text}")
    return response


async def _token(client: httpx.AsyncClient, email: str) -> str:
    response = await _request(
        client,
        "POST",
        "/v1/auth/token",
        json_body={
            "email": email,
            "password": DEMO_PASSWORD,
            "brand_slug": DEMO_BRAND_SLUG,
        },
    )
    return str(response.json()["access_token"])


async def _register_creator(
    client: httpx.AsyncClient, *, email: str, name: str, handle: str
) -> str:
    await _request(
        client,
        "POST",
        "/v1/auth/register",
        json_body={
            "email": email,
            "password": DEMO_PASSWORD,
            "display_name": name,
            "socials": [{"network": "instagram", "handle": handle}],
        },
    )
    response = await _request(
        client,
        "POST",
        "/v1/auth/token",
        json_body={"email": email, "password": DEMO_PASSWORD},
    )
    return str(response.json()["access_token"])


async def _activate_creator(
    client: httpx.AsyncClient,
    *,
    creator_token: str,
    owner_token: str,
    program_id: str,
    terms_id: str,
    motivation: str,
) -> tuple[str, list[dict[str, Any]]]:
    application = (
        await _request(
            client,
            "POST",
            f"/v1/programs/{program_id}/applications",
            token=creator_token,
            json_body={"motivation": motivation},
        )
    ).json()
    reviewed = (
        await _request(
            client,
            "POST",
            f"/v1/applications/{application['id']}/review",
            token=owner_token,
            json_body={"decision": "approved", "note": "Approved by local demo"},
        )
    ).json()
    membership_id = str(reviewed["membership"]["id"])
    accepted = (
        await _request(
            client,
            "POST",
            f"/v1/memberships/{membership_id}/terms-acceptances",
            token=creator_token,
            json_body={"terms_id": terms_id},
        )
    ).json()
    return membership_id, list(accepted["assets"])


async def run_demo() -> dict[str, Any]:
    await seed_database()
    suffix = f"{int(time.time())}-{uuid.uuid4().hex[:6]}"
    now = datetime.now(UTC)
    async with httpx.AsyncClient(base_url=API_URL, timeout=10.0) as client:
        owner_token = await _token(client, "owner@creatorops.dev")
        finance_token = await _token(client, "finance@creatorops.dev")
        creator_a_token = await _register_creator(
            client,
            email=f"alice-{suffix}@creatorops.dev",
            name="Alice Creator",
            handle=f"alice_{suffix}",
        )
        creator_b_token = await _register_creator(
            client,
            email=f"bruno-{suffix}@creatorops.dev",
            name="Bruno Creator",
            handle=f"bruno_{suffix}",
        )

        program = (
            await _request(
                client,
                "POST",
                "/v1/programs",
                token=owner_token,
                json_body={
                    "name": f"Local Creator Program {suffix}",
                    "slug": f"local-{suffix}",
                    "attribution_window_days": 30,
                    "return_window_days": 0,
                    "payout_minimum": "1.00",
                },
            )
        ).json()
        program_id = str(program["id"])
        terms = (
            await _request(
                client,
                "POST",
                f"/v1/programs/{program_id}/terms",
                token=owner_token,
                json_body={
                    "content": "CreatorOps demonstration terms, versioned and locally accepted.",
                    "required": True,
                },
            )
        ).json()
        await _request(
            client,
            "POST",
            f"/v1/programs/{program_id}/commission-plans",
            token=finance_token,
            json_body={
                "base_rate": "0.10",
                "return_window_days": 0,
                "payout_minimum": "1.00",
                "active_from": (now - timedelta(minutes=1)).isoformat(),
                "tiers": [
                    {"threshold_gmv": "100.00", "rate": "0.12"},
                    {"threshold_gmv": "500.00", "rate": "0.15"},
                ],
                "bonuses": [
                    {
                        "name": "First 200 BRL",
                        "metric": "gmv",
                        "threshold": "200.00",
                        "amount": "5.00",
                    }
                ],
            },
        )
        await _request(
            client,
            "POST",
            f"/v1/programs/{program_id}/status",
            token=owner_token,
            json_body={"status": "active"},
        )
        campaign = (
            await _request(
                client,
                "POST",
                f"/v1/programs/{program_id}/campaigns",
                token=owner_token,
                json_body={
                    "name": f"Launch {suffix}",
                    "briefing": "Local campaign used by the end-to-end interview demo.",
                    "starts_at": now.isoformat(),
                    "ends_at": (now + timedelta(days=30)).isoformat(),
                },
            )
        ).json()
        await _request(
            client,
            "POST",
            f"/v1/campaigns/{campaign['id']}/status",
            token=owner_token,
            json_body={"status": "active"},
        )
        await _request(
            client,
            "POST",
            f"/v1/programs/{program_id}/commission-plans",
            token=finance_token,
            json_body={
                "campaign_id": str(campaign["id"]),
                "base_rate": "0.20",
                "return_window_days": 0,
                "payout_minimum": "1.00",
                "active_from": (now - timedelta(minutes=1)).isoformat(),
                "tiers": [],
                "bonuses": [],
            },
        )

        membership_a, assets_a = await _activate_creator(
            client,
            creator_token=creator_a_token,
            owner_token=owner_token,
            program_id=program_id,
            terms_id=str(terms["id"]),
            motivation="I create practical technology content.",
        )
        membership_b, _assets_b = await _activate_creator(
            client,
            creator_token=creator_b_token,
            owner_token=owner_token,
            program_id=program_id,
            terms_id=str(terms["id"]),
            motivation="I create backend architecture content.",
        )
        await _request(
            client,
            "POST",
            f"/v1/campaigns/{campaign['id']}/participants",
            token=owner_token,
            json_body={"membership_ids": [membership_a, membership_b]},
        )
        assets_a = (
            await _request(
                client,
                "GET",
                f"/v1/memberships/{membership_a}/assets",
                token=creator_a_token,
            )
        ).json()
        assets_b = (
            await _request(
                client,
                "GET",
                f"/v1/memberships/{membership_b}/assets",
                token=creator_b_token,
            )
        ).json()
        coupon_a = next(
            asset
            for asset in assets_a
            if asset["asset_type"] == "coupon" and asset["campaign_id"] == str(campaign["id"])
        )
        link_b = next(
            asset
            for asset in assets_b
            if asset["asset_type"] == "link" and asset["campaign_id"] == str(campaign["id"])
        )
        click = await _request(client, "GET", f"/r/{link_b['code']}?visitor=demo-shopper")
        click_id = click.headers["X-CreatorOps-Click-ID"]

        webhook = {
            "event_id": f"evt-paid-{suffix}",
            "event_type": "order.paid",
            "order_id": f"order-{suffix}",
            "occurred_at": now.isoformat(),
            "amount": "200.00",
            "currency": "BRL",
            "coupon_code": coupon_a["code"],
            "click_id": click_id,
        }
        raw = json.dumps(webhook, separators=(",", ":")).encode()
        signature = hmac.new(
            settings.commerce_webhook_secret.encode(), raw, hashlib.sha256
        ).hexdigest()
        order_result = (
            await _request(
                client,
                "POST",
                f"/v1/webhooks/commerce/{DEMO_BRAND_SLUG}",
                content=raw,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                },
            )
        ).json()
        replay_result = (
            await _request(
                client,
                "POST",
                f"/v1/webhooks/commerce/{DEMO_BRAND_SLUG}",
                content=raw,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": f"sha256={signature}",
                },
            )
        ).json()

        await _request(
            client,
            "POST",
            "/v1/listening/imports",
            token=owner_token,
            json_body={
                "posts": [
                    {
                        "network": "instagram",
                        "external_post_id": f"ig-{suffix}",
                        "handle": f"alice_{suffix}",
                        "program_id": program_id,
                        "campaign_id": str(campaign["id"]),
                        "published_at": now.isoformat(),
                        "caption": "CreatorOps local campaign post",
                        "url": "https://example.test/local-post",
                        "metrics": {"likes": 321, "comments": 18, "views": 4200},
                    }
                ]
            },
        )
        content_rows: list[dict[str, Any]] = []
        for _ in range(30):
            content_page = (await _request(client, "GET", "/v1/posts", token=owner_token)).json()
            content_rows = [
                row for row in content_page["items"] if row["external_post_id"] == f"ig-{suffix}"
            ]
            if content_rows:
                break
            await asyncio.sleep(0.25)
        if not content_rows:
            raise DemoFailure("Worker did not ingest the social post")
        await _request(
            client,
            "POST",
            f"/v1/posts/{content_rows[0]['id']}/review",
            token=owner_token,
            json_body={"decision": "approved"},
        )
        await _request(
            client,
            "POST",
            "/v1/listening/imports",
            token=owner_token,
            json_body={
                "posts": [
                    {
                        "network": "instagram",
                        "external_post_id": f"ig-{suffix}",
                        "handle": f"alice_{suffix}",
                        "program_id": program_id,
                        "campaign_id": str(campaign["id"]),
                        "published_at": now.isoformat(),
                        "caption": "CreatorOps metrics refresh",
                        "url": "https://example.test/local-post",
                        "metrics": {"likes": 400, "comments": 22, "views": 5000},
                    }
                ]
            },
        )
        refreshed_content: dict[str, Any] = {}
        for _ in range(30):
            refreshed_content = (
                await _request(
                    client,
                    "GET",
                    f"/v1/posts/{content_rows[0]['id']}",
                    token=owner_token,
                )
            ).json()
            if refreshed_content["metrics"].get("views") == 5000:
                break
            await asyncio.sleep(0.25)
        if refreshed_content.get("status") != "approved":
            raise DemoFailure("Social reimport erased the human review")

        settlement_at = now + timedelta(days=1)
        await _request(
            client,
            "POST",
            "/v1/commissions/settle",
            token=finance_token,
            json_body={"as_of": settlement_at.isoformat()},
        )
        batch_payload = (
            await _request(
                client,
                "POST",
                "/v1/payout-batches",
                token=finance_token,
                json_body={
                    "program_id": program_id,
                    "cutoff_at": (settlement_at + timedelta(minutes=1)).isoformat(),
                    "scenario": "timeout_after",
                },
            )
        ).json()
        batch_id = str(batch_payload["batch"]["id"])
        approved_batch = (
            await _request(
                client,
                "POST",
                f"/v1/payout-batches/{batch_id}/approve",
                token=finance_token,
                json_body={"comment": "Approved for local reconciliation demo"},
            )
        ).json()
        payout_id = str(approved_batch["payouts"][0]["id"])
        payout_status = "pending"
        for _ in range(40):
            batch_state = (
                await _request(
                    client,
                    "GET",
                    f"/v1/payout-batches/{batch_id}",
                    token=finance_token,
                )
            ).json()
            payout_status = str(batch_state["payouts"][0]["status"])
            if payout_status == "unknown":
                break
            await asyncio.sleep(0.25)
        if payout_status != "unknown":
            raise DemoFailure(f"Expected unknown payout, got {payout_status}")

        await _request(client, "POST", "/v1/reconciliation/runs", token=finance_token)
        findings = (
            await _request(
                client,
                "GET",
                "/v1/agent/findings?finding_state=open",
                token=finance_token,
            )
        ).json()
        finding = next(row for row in findings["items"] if row["payout_id"] == payout_id)
        proposal = (
            await _request(
                client,
                "POST",
                f"/v1/agent/findings/{finding['id']}/proposals",
                token=finance_token,
            )
        ).json()
        gate = (
            await _request(
                client,
                "POST",
                f"/v1/agent/proposals/{proposal['id']}/gate",
                token=finance_token,
            )
        ).json()
        await _request(
            client,
            "POST",
            f"/v1/agent/proposals/{proposal['id']}/approve",
            token=finance_token,
            json_body={"comment": "Provider evidence reviewed and approved"},
        )
        executed = (
            await _request(
                client,
                "POST",
                f"/v1/agent/proposals/{proposal['id']}/execute",
                token=finance_token,
            )
        ).json()
        report = (
            await _request(
                client,
                "GET",
                f"/v1/reports/programs/{program_id}/overview",
                token=owner_token,
            )
        ).json()
        campaign_report = (
            await _request(
                client,
                "GET",
                f"/v1/reports/campaigns/{campaign['id']}/overview",
                token=owner_token,
            )
        ).json()
        membership_report = (
            await _request(
                client,
                "GET",
                f"/v1/reports/memberships/{membership_a}/overview",
                token=creator_a_token,
            )
        ).json()
        balance = (
            await _request(
                client,
                "GET",
                f"/v1/memberships/{membership_a}/balance",
                token=creator_a_token,
            )
        ).json()
        return {
            "program_id": program_id,
            "campaign_id": str(campaign["id"]),
            "coupon_won_conflict": order_result["attribution"] == "coupon",
            "webhook_replay_idempotent": replay_result["duplicate"] is True,
            "payout_before_reconciliation": "unknown",
            "finding_type": finding["finding_type"],
            "gate_result": gate["gate"]["result"],
            "proposal_state": executed["state"],
            "content_review_preserved_after_reimport": refreshed_content["status"] == "approved",
            "report": report,
            "campaign_report": campaign_report,
            "membership_report": membership_report,
            "creator_balance": balance,
        }


def run() -> None:
    result = asyncio.run(run_demo())
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
