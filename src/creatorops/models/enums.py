from enum import StrEnum


class UserKind(StrEnum):
    STAFF = "staff"
    CREATOR = "creator"


class BrandRole(StrEnum):
    OWNER = "owner"
    OPS = "ops"
    FINANCE = "finance"


class SocialNetwork(StrEnum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ProgramStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationSource(StrEnum):
    SELF = "self"
    INVITE = "invite"


class MembershipStatus(StrEnum):
    AWAITING_TERMS = "awaiting_terms"
    ACTIVE = "active"
    PAUSED = "paused"
    OFFBOARDED = "offboarded"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AssetType(StrEnum):
    COUPON = "coupon"
    LINK = "link"


class CommerceEventType(StrEnum):
    CREATED = "order.created"
    PAID = "order.paid"
    CANCELLED = "order.cancelled"
    REFUNDED = "order.refunded"


class WebhookProcessingStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    IGNORED = "ignored"


class OrderStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    CANCELLED = "cancelled"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"


class AttributionReason(StrEnum):
    COUPON = "coupon"
    LAST_CLICK = "last_click"
    UNATTRIBUTED = "unattributed"
    MANUAL = "manual"


class CommissionMetric(StrEnum):
    GMV = "gmv"
    ORDERS = "orders"


class CommissionKind(StrEnum):
    SALE = "sale"
    BONUS = "bonus"
    REFUND_ADJUSTMENT = "refund_adjustment"


class CommissionStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    REVERSED = "reversed"


class LedgerBucket(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    RESERVED = "reserved"
    PAID = "paid"


class LedgerEntryType(StrEnum):
    COMMISSION_ACCRUED = "commission_accrued"
    COMMISSION_SETTLED = "commission_settled"
    COMMISSION_REVERSED = "commission_reversed"
    PAYOUT_RESERVED = "payout_reserved"
    PAYOUT_CONFIRMED = "payout_confirmed"
    PAYOUT_RELEASED = "payout_released"
    RECONCILIATION_ADJUSTMENT = "reconciliation_adjustment"


class PayoutBatchStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_FAILED = "partially_failed"
    CANCELLED = "cancelled"


class PayoutStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ProviderScenario(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT_BEFORE = "timeout_before"
    TIMEOUT_AFTER = "timeout_after"


class ReconciliationRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingType(StrEnum):
    PROVIDER_CONFIRMED_INTERNAL_UNKNOWN = "provider_confirmed_internal_unknown"
    PROVIDER_MISSING_INTERNAL_UNKNOWN = "provider_missing_internal_unknown"
    AMOUNT_MISMATCH = "amount_mismatch"
    DUPLICATE_PROVIDER_TRANSFER = "duplicate_provider_transfer"
    LEDGER_BALANCE_MISMATCH = "ledger_balance_mismatch"


class FindingState(StrEnum):
    OPEN = "open"
    PROPOSED = "proposed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ProposalAction(StrEnum):
    CONFIRM_PAYOUT = "confirm_payout"
    MARK_FAILED_RELEASE = "mark_failed_release"
    COMPENSATING_ADJUSTMENT = "compensating_adjustment"
    MANUAL_REVIEW = "manual_review"


class ProposalState(StrEnum):
    DRAFT = "draft"
    GATED = "gated"
    BLOCKED = "blocked"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    STALE = "stale"


class GateResult(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class ContentStatus(StrEnum):
    DETECTED = "detected"
    MATCHED = "matched"
    APPROVED = "approved"
    REJECTED = "rejected"
