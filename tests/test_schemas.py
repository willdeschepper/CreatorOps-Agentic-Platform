from datetime import datetime

import pytest
from pydantic import ValidationError

from creatorops.schemas import CommerceWebhookRequest, SocialPostInput


def test_financial_event_requires_timezone_and_refund_value() -> None:
    with pytest.raises(ValidationError):
        CommerceWebhookRequest(
            event_id="evt-1",
            event_type="order.refunded",
            order_id="order-1",
            occurred_at=datetime(2026, 1, 1),
            amount="100.00",
            refunded_amount=None,
        )


def test_social_metrics_cannot_be_negative() -> None:
    with pytest.raises(ValidationError, match="cannot be negative"):
        SocialPostInput(
            network="instagram",
            external_post_id="post-1",
            handle="creator",
            program_id="018f0de5-54fd-7b4a-bd15-2f5ad811bd18",
            published_at="2026-01-01T00:00:00Z",
            metrics={"likes": -1},
        )
