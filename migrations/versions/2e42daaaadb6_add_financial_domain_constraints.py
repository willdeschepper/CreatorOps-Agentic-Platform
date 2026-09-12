"""add financial domain constraints

Revision ID: 2e42daaaadb6
Revises: 8012c4276b8b
Create Date: 2026-09-11 23:39:07.261485
"""

from collections.abc import Sequence

from alembic import op

revision: str = "2e42daaaadb6"
down_revision: str | None = "8012c4276b8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CONSTRAINTS = (
    ("ck_programs_attribution_window_positive", "programs", "attribution_window_days > 0"),
    ("ck_programs_return_window_non_negative", "programs", "return_window_days >= 0"),
    ("ck_programs_payout_minimum_positive", "programs", "payout_minimum > 0"),
    (
        "ck_campaigns_campaign_dates_ordered",
        "campaigns",
        "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
    ),
    ("ck_orders_order_gross_positive", "orders", "gross_amount > 0"),
    ("ck_orders_order_refund_non_negative", "orders", "refunded_amount >= 0"),
    ("ck_orders_order_refund_within_gross", "orders", "refunded_amount <= gross_amount"),
    (
        "ck_commission_plans_base_rate_valid",
        "commission_plans",
        "base_rate >= 0 AND base_rate <= 1",
    ),
    (
        "ck_commission_plans_plan_return_window_non_negative",
        "commission_plans",
        "return_window_days >= 0",
    ),
    (
        "ck_commission_plans_plan_payout_minimum_positive",
        "commission_plans",
        "payout_minimum > 0",
    ),
    (
        "ck_commission_tiers_tier_threshold_non_negative",
        "commission_tiers",
        "threshold_gmv >= 0",
    ),
    (
        "ck_commission_tiers_tier_rate_valid",
        "commission_tiers",
        "rate >= 0 AND rate <= 1",
    ),
    ("ck_bonus_rules_bonus_threshold_positive", "bonus_rules", "threshold > 0"),
    ("ck_bonus_rules_bonus_amount_positive", "bonus_rules", "amount > 0"),
    (
        "ck_commissions_commission_rate_valid",
        "commissions",
        "rate >= 0 AND rate <= 1",
    ),
    ("ck_commissions_commission_period_key_length", "commissions", "length(period_key) = 7"),
    ("ck_payouts_payout_amount_positive", "payouts", "amount > 0"),
    ("ck_payouts_payout_version_positive", "payouts", "version >= 1"),
)


def upgrade() -> None:
    for name, table, condition in CONSTRAINTS:
        op.create_check_constraint(name, table, condition)


def downgrade() -> None:
    for name, table, _condition in reversed(CONSTRAINTS):
        op.drop_constraint(name, table, type_="check")
