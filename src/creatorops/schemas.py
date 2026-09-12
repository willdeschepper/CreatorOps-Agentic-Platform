import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from creatorops.models.enums import (
    ApplicationStatus,
    AssetType,
    AttributionReason,
    BrandRole,
    CampaignParticipantStatus,
    CampaignStatus,
    CommerceEventType,
    CommissionKind,
    CommissionStatus,
    ContentStatus,
    FindingState,
    FindingType,
    InvitationStatus,
    LedgerBucket,
    LedgerEntryType,
    MembershipStatus,
    OrderStatus,
    PayoutBatchStatus,
    PayoutStatus,
    ProgramStatus,
    ProposalAction,
    ProposalState,
    ProviderScenario,
    SocialNetwork,
    UserKind,
)

Money = Annotated[Decimal, Field(max_digits=14, decimal_places=2)]
NonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2)]
Rate = Annotated[Decimal, Field(ge=0, le=1, max_digits=7, decimal_places=6)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageResponse[PageItem](BaseModel):
    items: list[PageItem]
    total: int
    limit: int
    offset: int


class SocialProfileInput(BaseModel):
    network: SocialNetwork
    handle: str = Field(min_length=1, max_length=120)


class RegisterCreatorRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=160)
    socials: list[SocialProfileInput] = Field(default_factory=list, max_length=2)


class CreatorRegistrationResponse(ORMModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    kind: UserKind


class TokenRequest(BaseModel):
    email: EmailStr
    password: str
    brand_slug: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    display_name: str
    kind: UserKind
    brand_id: uuid.UUID | None
    role: BrandRole | None
    socials: list["SocialProfileResponse"] = Field(default_factory=list)


class ProgramCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    attribution_window_days: int = Field(default=30, ge=1, le=365)
    return_window_days: int = Field(default=7, ge=0, le=180)
    payout_minimum: PositiveMoney = Decimal("100.00")


class ProgramResponse(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    slug: str
    status: ProgramStatus
    attribution_window_days: int
    return_window_days: int
    payout_minimum: Money
    currency: str
    created_at: datetime


class ProgramStatusRequest(BaseModel):
    status: ProgramStatus


class TermsCreateRequest(BaseModel):
    content: str = Field(min_length=20)
    required: bool = True


class TermsResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    version: int
    content: str
    required: bool
    published_at: datetime


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    briefing: str = ""
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("starts_at", "ends_at")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("ends_at must include a timezone")
        return value


class CampaignResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    name: str
    status: CampaignStatus
    briefing: str
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime


class CampaignStatusRequest(BaseModel):
    status: CampaignStatus


class CommissionTierInput(BaseModel):
    threshold_gmv: NonNegativeMoney = Decimal("0.00")
    rate: Rate


class BonusRuleInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    metric: Literal["gmv", "orders"]
    threshold: PositiveMoney
    amount: PositiveMoney


class CommissionPlanCreateRequest(BaseModel):
    campaign_id: uuid.UUID | None = None
    base_rate: Rate
    return_window_days: int = Field(default=7, ge=0, le=180)
    payout_minimum: PositiveMoney = Decimal("100.00")
    active_from: datetime
    tiers: list[CommissionTierInput] = Field(default_factory=list)
    bonuses: list[BonusRuleInput] = Field(default_factory=list)

    @field_validator("active_from")
    @classmethod
    def active_from_timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("active_from must include a timezone")
        return value


class CommissionPlanResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    campaign_id: uuid.UUID | None
    version: int
    base_rate: Rate
    return_window_days: int
    payout_minimum: Money
    active_from: datetime


class CommissionTierResponse(ORMModel):
    id: uuid.UUID
    threshold_gmv: Money
    rate: Rate


class BonusRuleResponse(ORMModel):
    id: uuid.UUID
    name: str
    metric: str
    threshold: Money
    amount: Money


class CommissionPlanDetailResponse(CommissionPlanResponse):
    tiers: list[CommissionTierResponse]
    bonuses: list[BonusRuleResponse]


class SocialProfileResponse(ORMModel):
    id: uuid.UUID
    network: SocialNetwork
    handle: str
    handle_normalized: str
    verified: bool


class CreatorSummary(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    socials: list[SocialProfileResponse] = Field(default_factory=list)


class ApplicationCreateRequest(BaseModel):
    motivation: str = Field(default="", max_length=3000)


class ApplicationReviewRequest(BaseModel):
    decision: Literal["in_review", "approved", "rejected"]
    note: str = Field(default="", max_length=3000)


class ApplicationResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    creator_id: uuid.UUID
    source: str
    status: ApplicationStatus
    motivation: str
    review_note: str | None
    created_at: datetime


class ApplicationDetailResponse(ApplicationResponse):
    program_name: str
    creator: CreatorSummary


class ApplicationReviewResponse(BaseModel):
    application: ApplicationResponse
    membership: "MembershipResponse | None"


class ApplicationWithdrawRequest(BaseModel):
    comment: str = Field(default="", max_length=2000)


class MembershipResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    creator_id: uuid.UUID
    status: MembershipStatus
    activated_at: datetime | None
    version: int


class MembershipStatusRequest(BaseModel):
    status: Literal["active", "paused", "offboarded"]
    comment: str = Field(min_length=3, max_length=2000)


class TermsAcceptanceRequest(BaseModel):
    terms_id: uuid.UUID


class AssetResponse(ORMModel):
    id: uuid.UUID
    membership_id: uuid.UUID
    campaign_id: uuid.UUID | None
    asset_type: AssetType
    code: str
    target_url: str | None
    active: bool


class TermsAcceptanceResponse(BaseModel):
    membership: MembershipResponse
    assets: list[AssetResponse]


class MembershipDetailResponse(MembershipResponse):
    program_name: str
    creator: CreatorSummary
    accepted_terms_version: int | None
    required_terms: TermsResponse | None
    assets: list[AssetResponse]
    balance: "BalanceResponse"


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    expires_in_hours: int = Field(default=168, ge=1, le=720)


class InvitationResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    email: EmailStr
    status: InvitationStatus
    expires_at: datetime
    used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class InvitationCreatedResponse(InvitationResponse):
    token: str
    acceptance_url: str


class InvitationInspectResponse(BaseModel):
    program_id: uuid.UUID
    program_name: str
    brand_name: str
    email_hint: str
    status: InvitationStatus
    expires_at: datetime


class InvitationAcceptResponse(BaseModel):
    invitation: InvitationResponse
    application: ApplicationResponse
    membership: MembershipResponse


class CampaignParticipantsRequest(BaseModel):
    membership_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)

    @field_validator("membership_ids")
    @classmethod
    def unique_memberships(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(set(value)) != len(value):
            raise ValueError("membership_ids must be unique")
        return value


class CampaignParticipantStatusRequest(BaseModel):
    status: CampaignParticipantStatus
    comment: str = Field(min_length=3, max_length=2000)


class CampaignParticipantResponse(ORMModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    membership_id: uuid.UUID
    status: CampaignParticipantStatus
    selected_by: uuid.UUID | None
    selected_at: datetime
    removed_at: datetime | None
    version: int


class CampaignParticipantDetailResponse(CampaignParticipantResponse):
    creator: CreatorSummary
    assets: list[AssetResponse]


class CommerceWebhookRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=160)
    event_type: CommerceEventType
    order_id: str = Field(min_length=1, max_length=160)
    occurred_at: datetime
    amount: PositiveMoney
    currency: Literal["BRL"] = "BRL"
    coupon_code: str | None = None
    click_id: uuid.UUID | None = None
    refunded_amount: NonNegativeMoney | None = None

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_refund(self) -> "CommerceWebhookRequest":
        if self.event_type == CommerceEventType.REFUNDED:
            if self.refunded_amount is None or self.refunded_amount <= 0:
                raise ValueError("order.refunded requires a positive refunded_amount")
            if self.refunded_amount > self.amount:
                raise ValueError("refunded_amount cannot exceed amount")
        return self


class WebhookResponse(BaseModel):
    event_id: str
    order_id: uuid.UUID | None
    status: str
    duplicate: bool = False
    attribution: str | None = None
    commission: Money | None = None


class BalanceResponse(BaseModel):
    membership_id: uuid.UUID
    pending: Money
    available: Money
    reserved: Money
    paid: Money


class PayoutBatchCreateRequest(BaseModel):
    program_id: uuid.UUID
    cutoff_at: datetime
    scenario: ProviderScenario = ProviderScenario.SUCCESS

    @field_validator("cutoff_at")
    @classmethod
    def cutoff_timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("cutoff_at must include a timezone")
        return value


class ApprovalRequest(BaseModel):
    comment: str = Field(min_length=3, max_length=2000)


class PayoutItemResponse(ORMModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    program_id: uuid.UUID
    membership_id: uuid.UUID
    amount: Money
    currency: str
    status: PayoutStatus
    provider_reference: str | None
    version: int
    created_at: datetime


class PayoutBatchResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    cutoff_at: datetime
    status: PayoutBatchStatus
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    created_at: datetime


class PayoutBatchDetailResponse(BaseModel):
    batch: PayoutBatchResponse
    payouts: list[PayoutItemResponse]


class PayoutBatchCancelRequest(BaseModel):
    comment: str = Field(min_length=3, max_length=2000)


class SocialPostInput(BaseModel):
    network: SocialNetwork
    external_post_id: str = Field(min_length=1, max_length=160)
    handle: str = Field(min_length=1, max_length=120)
    program_id: uuid.UUID
    campaign_id: uuid.UUID | None = None
    published_at: datetime
    caption: str = Field(default="", max_length=10000)
    url: HttpUrl | None = None
    metrics: dict[str, int] = Field(default_factory=dict)

    @field_validator("published_at")
    @classmethod
    def published_at_timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("published_at must include a timezone")
        return value

    @field_validator("metrics")
    @classmethod
    def metrics_must_be_non_negative(cls, value: dict[str, int]) -> dict[str, int]:
        if any(metric < 0 for metric in value.values()):
            raise ValueError("social metrics cannot be negative")
        return value


class SocialImportRequest(BaseModel):
    posts: list[SocialPostInput] = Field(min_length=1, max_length=500)


class SocialImportResponse(BaseModel):
    status: Literal["queued"]
    posts: int


class ContentReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]


class ContentEvidenceResponse(ORMModel):
    id: uuid.UUID
    network: SocialNetwork
    external_post_id: str
    membership_id: uuid.UUID | None
    status: ContentStatus
    published_at: datetime
    metrics: dict[str, object]


class ContentEvidenceDetailResponse(ContentEvidenceResponse):
    brand_id: uuid.UUID
    program_id: uuid.UUID
    campaign_id: uuid.UUID | None
    handle_normalized: str
    firestore_path: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class ReconciliationRunResponse(ORMModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    started_by: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    summary: dict[str, object]


class FindingResponse(ORMModel):
    id: uuid.UUID
    run_id: uuid.UUID
    payout_id: uuid.UUID
    finding_type: FindingType
    state: FindingState
    evidence: dict[str, object]
    evidence_hash: str
    payout_version: int
    created_at: datetime
    resolved_at: datetime | None


class ProposalResponse(ORMModel):
    id: uuid.UUID
    finding_id: uuid.UUID
    action: ProposalAction
    state: ProposalState
    rationale: str
    risk: str
    proposed_changes: dict[str, object]
    payout_version: int
    created_at: datetime


class ProposalDetailResponse(ProposalResponse):
    evidence_hash: str
    approved_by: uuid.UUID | None
    approval_comment: str | None
    approved_at: datetime | None
    rejected_by: uuid.UUID | None
    rejection_comment: str | None
    rejected_at: datetime | None
    executed_at: datetime | None
    gates: list["GateRunResponse"]


class RejectRequest(BaseModel):
    comment: str = Field(min_length=3, max_length=2000)


class SettlementRequest(BaseModel):
    as_of: datetime | None = None

    @field_validator("as_of")
    @classmethod
    def as_of_timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("as_of must include a timezone")
        return value


class SettlementResponse(BaseModel):
    settled: int


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(HealthResponse):
    database: str


class GateRunResponse(ORMModel):
    id: uuid.UUID
    proposal_id: uuid.UUID
    result: str
    checks: list[dict[str, object]]
    created_at: datetime


class GateResponse(BaseModel):
    proposal: ProposalResponse
    gate: GateRunResponse


class FindingDismissRequest(BaseModel):
    comment: str = Field(min_length=3, max_length=2000)


class OrderResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID | None
    external_id: str
    status: OrderStatus
    gross_amount: Money
    refunded_amount: Money
    currency: str
    paid_at: datetime | None
    created_at: datetime


class OrderAttributionResponse(ORMModel):
    id: uuid.UUID
    membership_id: uuid.UUID | None
    campaign_id: uuid.UUID | None
    coupon_asset_id: uuid.UUID | None
    click_id: uuid.UUID | None
    reason: AttributionReason
    signals: dict[str, object]
    attributed_at: datetime


class CommissionResponse(ORMModel):
    id: uuid.UUID
    order_id: uuid.UUID
    membership_id: uuid.UUID
    plan_id: uuid.UUID
    plan_version: int
    kind: CommissionKind
    status: CommissionStatus
    gross_basis: Money
    rate: Rate
    amount: Money
    period_key: str
    eligible_at: datetime
    available_at: datetime | None
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    attribution: OrderAttributionResponse | None
    commissions: list[CommissionResponse]


class LedgerEntryResponse(ORMModel):
    id: uuid.UUID
    program_id: uuid.UUID
    membership_id: uuid.UUID
    commission_id: uuid.UUID | None
    payout_id: uuid.UUID | None
    bucket: LedgerBucket
    entry_type: LedgerEntryType
    amount: Money
    currency: str
    idempotency_key: str
    description: str
    created_at: datetime


class AuditLogResponse(ORMModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    data: dict[str, object]
    created_at: datetime


class ReportOverviewResponse(BaseModel):
    program_id: uuid.UUID
    gmv: Money
    refunded_gmv: Money
    net_gmv: Money
    orders: int
    attributed_orders: int
    active_creators: int
    approved_posts: int
    commission_pending: Money
    commission_available: Money
    commission_reserved: Money
    commission_paid: Money
    payouts: dict[str, int]
    social_metrics: dict[str, int] = Field(default_factory=dict)


class CampaignReportResponse(BaseModel):
    campaign_id: uuid.UUID
    program_id: uuid.UUID
    gmv: Money
    refunded_gmv: Money
    net_gmv: Money
    orders: int
    selected_creators: int
    approved_posts: int
    social_metrics: dict[str, int]
    commission_accrued: Money
    commission_adjustments: Money
    net_commission: Money


class MembershipReportResponse(BaseModel):
    membership_id: uuid.UUID
    program_id: uuid.UUID
    gmv: Money
    refunded_gmv: Money
    net_gmv: Money
    orders: int
    approved_posts: int
    social_metrics: dict[str, int]
    commission_pending: Money
    commission_available: Money
    commission_reserved: Money
    commission_paid: Money
    payouts: dict[str, int]
