import uuid
from datetime import datetime
from typing import cast

from sqlalchemy import exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.errors import ConflictError, NotFoundError, UnprocessableError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.commissions import BonusRule, CommissionPlan, CommissionTier
from creatorops.models.enums import (
    CampaignParticipantStatus,
    CampaignStatus,
    CommissionMetric,
    MembershipStatus,
    ProgramStatus,
)
from creatorops.models.partnerships import AffiliateAsset, CampaignParticipant, ProgramMembership
from creatorops.models.programs import Campaign, Program, ProgramTerms
from creatorops.schemas import (
    CampaignCreateRequest,
    CommissionPlanCreateRequest,
    ProgramCreateRequest,
    TermsCreateRequest,
)
from creatorops.services.shared import add_audit


async def get_program_for_brand(
    session: AsyncSession, program_id: uuid.UUID, brand_id: uuid.UUID
) -> Program:
    program = await session.scalar(
        select(Program).where(Program.id == program_id, Program.brand_id == brand_id)
    )
    if program is None:
        raise NotFoundError("program_not_found", "Program was not found in the active brand")
    return program


async def create_program(
    session: AsyncSession, principal: Principal, request: ProgramCreateRequest
) -> Program:
    assert principal.brand_id is not None
    program = Program(
        brand_id=principal.brand_id,
        name=request.name.strip(),
        slug=request.slug,
        attribution_window_days=request.attribution_window_days,
        return_window_days=request.return_window_days,
        payout_minimum=request.payout_minimum,
        status=ProgramStatus.DRAFT,
    )
    now = clock.now()
    try:
        async with session.begin():
            session.add(program)
            await session.flush()
            add_audit(
                session,
                brand_id=principal.brand_id,
                actor_user_id=principal.user_id,
                action="program.created",
                entity_type="program",
                entity_id=program.id,
                data={"slug": program.slug},
                now=now,
            )
    except IntegrityError as exc:
        raise ConflictError(
            "program_slug_exists", "This brand already uses the program slug"
        ) from exc
    return program


async def list_programs(
    session: AsyncSession,
    brand_id: uuid.UUID,
    *,
    status: ProgramStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[Program], int]:
    filters = [Program.brand_id == brand_id]
    if status:
        filters.append(Program.status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(Program).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Program)
                .where(*filters)
                .order_by(Program.created_at.desc(), Program.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def discover_programs(
    session: AsyncSession, *, limit: int, offset: int
) -> tuple[list[Program], int]:
    filters = [Program.status == ProgramStatus.ACTIVE]
    total = int(
        await session.scalar(select(func.count()).select_from(Program).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Program)
                .where(*filters)
                .order_by(Program.name, Program.id)
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_visible_program(
    session: AsyncSession, *, principal: Principal, program_id: uuid.UUID
) -> Program:
    if principal.brand_id is not None:
        return await get_program_for_brand(session, program_id, principal.brand_id)
    program = await session.get(Program, program_id)
    if program is None:
        raise NotFoundError("program_not_found", "Program was not found")
    membership = await session.scalar(
        select(ProgramMembership.id).where(
            ProgramMembership.program_id == program_id,
            ProgramMembership.creator_id == principal.user_id,
        )
    )
    if program.status != ProgramStatus.ACTIVE and membership is None:
        raise NotFoundError("program_not_found", "Program was not found")
    return program


async def get_campaign_for_brand(
    session: AsyncSession, *, brand_id: uuid.UUID, campaign_id: uuid.UUID
) -> Campaign:
    campaign = await session.scalar(
        select(Campaign)
        .join(Program, Program.id == Campaign.program_id)
        .where(Campaign.id == campaign_id, Program.brand_id == brand_id)
    )
    if campaign is None:
        raise NotFoundError("campaign_not_found", "Campaign was not found")
    return campaign


async def get_visible_campaign(
    session: AsyncSession, *, principal: Principal, campaign_id: uuid.UUID
) -> Campaign:
    campaign = await session.get(Campaign, campaign_id)
    if campaign is None:
        raise NotFoundError("campaign_not_found", "Campaign was not found")
    await get_visible_program(session, principal=principal, program_id=campaign.program_id)
    return campaign


async def list_campaigns(
    session: AsyncSession,
    *,
    principal: Principal,
    program_id: uuid.UUID,
    status: CampaignStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[Campaign], int]:
    await get_visible_program(session, principal=principal, program_id=program_id)
    filters = [Campaign.program_id == program_id]
    if status:
        filters.append(Campaign.status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(Campaign).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(Campaign)
                .where(*filters)
                .order_by(Campaign.created_at.desc(), Campaign.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_terms(
    session: AsyncSession,
    *,
    principal: Principal,
    program_id: uuid.UUID,
    limit: int,
    offset: int,
) -> tuple[list[ProgramTerms], int]:
    await get_visible_program(session, principal=principal, program_id=program_id)
    filters = [ProgramTerms.program_id == program_id]
    total = int(
        await session.scalar(select(func.count()).select_from(ProgramTerms).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(ProgramTerms)
                .where(*filters)
                .order_by(ProgramTerms.version.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_commission_plans(
    session: AsyncSession,
    *,
    principal: Principal,
    program_id: uuid.UUID,
    limit: int,
    offset: int,
) -> tuple[list[CommissionPlan], int]:
    await get_visible_program(session, principal=principal, program_id=program_id)
    filters = [CommissionPlan.program_id == program_id]
    total = int(
        await session.scalar(select(func.count()).select_from(CommissionPlan).where(*filters)) or 0
    )
    rows = list(
        (
            await session.scalars(
                select(CommissionPlan)
                .where(*filters)
                .order_by(CommissionPlan.active_from.desc(), CommissionPlan.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_commission_plan_detail(
    session: AsyncSession, *, principal: Principal, plan_id: uuid.UUID
) -> tuple[CommissionPlan, list[CommissionTier], list[BonusRule]]:
    plan = await session.get(CommissionPlan, plan_id)
    if plan is None:
        raise NotFoundError("commission_plan_not_found", "Commission plan was not found")
    await get_visible_program(session, principal=principal, program_id=plan.program_id)
    tiers = list(
        (
            await session.scalars(
                select(CommissionTier)
                .where(CommissionTier.plan_id == plan.id)
                .order_by(CommissionTier.threshold_gmv)
            )
        ).all()
    )
    bonuses = list(
        (await session.scalars(select(BonusRule).where(BonusRule.plan_id == plan.id))).all()
    )
    return plan, tiers, bonuses


async def change_program_status(
    session: AsyncSession,
    principal: Principal,
    program_id: uuid.UUID,
    target: ProgramStatus,
) -> Program:
    assert principal.brand_id is not None
    transitions: dict[ProgramStatus, set[ProgramStatus]] = {
        ProgramStatus.DRAFT: {ProgramStatus.ACTIVE, ProgramStatus.CLOSED},
        ProgramStatus.ACTIVE: {ProgramStatus.PAUSED, ProgramStatus.CLOSED},
        ProgramStatus.PAUSED: {ProgramStatus.ACTIVE, ProgramStatus.CLOSED},
    }
    async with session.begin():
        program = await session.scalar(
            select(Program)
            .where(Program.id == program_id, Program.brand_id == principal.brand_id)
            .with_for_update()
        )
        if program is None:
            raise NotFoundError("program_not_found", "Program was not found")
        if program.status == target:
            return program
        if target not in transitions.get(program.status, set()):
            raise ConflictError(
                "invalid_program_transition",
                f"Cannot transition program from {program.status.value} to {target.value}",
            )
        if target == ProgramStatus.ACTIVE:
            terms = await session.scalar(
                select(ProgramTerms.id).where(
                    ProgramTerms.program_id == program.id,
                    ProgramTerms.required.is_(True),
                )
            )
            plan = await session.scalar(
                select(CommissionPlan.id).where(
                    CommissionPlan.program_id == program.id,
                    CommissionPlan.campaign_id.is_(None),
                )
            )
            if terms is None or plan is None:
                raise ConflictError(
                    "program_not_ready",
                    "An active program requires published terms and a default commission plan",
                )
        previous = program.status
        program.status = target
        if target in {ProgramStatus.PAUSED, ProgramStatus.CLOSED}:
            await session.execute(
                update(AffiliateAsset)
                .where(
                    AffiliateAsset.membership_id.in_(
                        select(ProgramMembership.id).where(
                            ProgramMembership.program_id == program.id
                        )
                    )
                )
                .values(active=False)
            )
        elif target == ProgramStatus.ACTIVE:
            await session.execute(
                update(AffiliateAsset)
                .where(
                    AffiliateAsset.membership_id.in_(
                        select(ProgramMembership.id).where(
                            ProgramMembership.program_id == program.id,
                            ProgramMembership.status == MembershipStatus.ACTIVE,
                        )
                    ),
                    AffiliateAsset.campaign_id.is_(None),
                )
                .values(active=True)
            )
            await session.execute(
                update(AffiliateAsset)
                .where(
                    AffiliateAsset.campaign_id.in_(
                        select(Campaign.id).where(
                            Campaign.program_id == program.id,
                            Campaign.status == CampaignStatus.ACTIVE,
                        )
                    ),
                    AffiliateAsset.membership_id.in_(
                        select(ProgramMembership.id).where(
                            ProgramMembership.program_id == program.id,
                            ProgramMembership.status == MembershipStatus.ACTIVE,
                        )
                    ),
                    exists(
                        select(CampaignParticipant.id).where(
                            CampaignParticipant.campaign_id == AffiliateAsset.campaign_id,
                            CampaignParticipant.membership_id == AffiliateAsset.membership_id,
                            CampaignParticipant.status == CampaignParticipantStatus.SELECTED,
                        )
                    ),
                )
                .values(active=True)
            )
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="program.status_changed",
            entity_type="program",
            entity_id=program.id,
            data={"from": previous.value, "to": target.value},
            now=clock.now(),
        )
    return program


async def publish_terms(
    session: AsyncSession,
    principal: Principal,
    program_id: uuid.UUID,
    request: TermsCreateRequest,
) -> ProgramTerms:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        await get_program_for_brand(session, program_id, principal.brand_id)
        current_version = await session.scalar(
            select(func.coalesce(func.max(ProgramTerms.version), 0)).where(
                ProgramTerms.program_id == program_id
            )
        )
        terms = ProgramTerms(
            program_id=program_id,
            version=int(current_version or 0) + 1,
            content=request.content,
            required=request.required,
            published_at=now,
        )
        session.add(terms)
        await session.flush()
        if request.required:
            memberships = (
                await session.scalars(
                    select(ProgramMembership).where(
                        ProgramMembership.program_id == program_id,
                        ProgramMembership.status == MembershipStatus.ACTIVE,
                    )
                )
            ).all()
            for membership in memberships:
                membership.status = MembershipStatus.AWAITING_TERMS
                membership.version += 1
                assets = (
                    await session.scalars(
                        select(AffiliateAsset).where(
                            AffiliateAsset.membership_id == membership.id,
                            AffiliateAsset.active.is_(True),
                        )
                    )
                ).all()
                for asset in assets:
                    asset.active = False
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="program.terms_published",
            entity_type="program_terms",
            entity_id=terms.id,
            data={"program_id": str(program_id), "version": terms.version},
            now=now,
        )
    return terms


async def create_campaign(
    session: AsyncSession,
    principal: Principal,
    program_id: uuid.UUID,
    request: CampaignCreateRequest,
) -> Campaign:
    assert principal.brand_id is not None
    if request.starts_at and request.ends_at and request.ends_at <= request.starts_at:
        raise UnprocessableError("invalid_campaign_period", "ends_at must be after starts_at")
    campaign = Campaign(
        program_id=program_id,
        name=request.name.strip(),
        briefing=request.briefing,
        starts_at=request.starts_at,
        ends_at=request.ends_at,
    )
    try:
        async with session.begin():
            await get_program_for_brand(session, program_id, principal.brand_id)
            session.add(campaign)
            await session.flush()
            add_audit(
                session,
                brand_id=principal.brand_id,
                actor_user_id=principal.user_id,
                action="campaign.created",
                entity_type="campaign",
                entity_id=campaign.id,
                data={"program_id": str(program_id)},
                now=clock.now(),
            )
    except IntegrityError as exc:
        raise ConflictError(
            "campaign_name_exists", "Campaign names must be unique inside a program"
        ) from exc
    return campaign


async def change_campaign_status(
    session: AsyncSession,
    principal: Principal,
    campaign_id: uuid.UUID,
    target: CampaignStatus,
) -> Campaign:
    assert principal.brand_id is not None
    transitions: dict[CampaignStatus, set[CampaignStatus]] = {
        CampaignStatus.DRAFT: {
            CampaignStatus.SCHEDULED,
            CampaignStatus.ACTIVE,
            CampaignStatus.CANCELLED,
        },
        CampaignStatus.SCHEDULED: {CampaignStatus.ACTIVE, CampaignStatus.CANCELLED},
        CampaignStatus.ACTIVE: {CampaignStatus.ENDED, CampaignStatus.CANCELLED},
    }
    async with session.begin():
        campaign = await session.scalar(
            select(Campaign)
            .join(Program, Program.id == Campaign.program_id)
            .where(Campaign.id == campaign_id, Program.brand_id == principal.brand_id)
            .with_for_update(of=Campaign)
        )
        if campaign is None:
            raise NotFoundError("campaign_not_found", "Campaign was not found")
        if campaign.status == target:
            return campaign
        if target not in transitions.get(campaign.status, set()):
            raise ConflictError(
                "invalid_campaign_transition",
                f"Cannot transition campaign from {campaign.status.value} to {target.value}",
            )
        program = await session.get(Program, campaign.program_id)
        assert program is not None
        if target == CampaignStatus.ACTIVE and program.status != ProgramStatus.ACTIVE:
            raise ConflictError("program_inactive", "Program must be active")
        previous = campaign.status
        campaign.status = target
        await session.execute(
            update(AffiliateAsset)
            .where(AffiliateAsset.campaign_id == campaign.id)
            .values(active=False)
        )
        if target == CampaignStatus.ACTIVE:
            await session.execute(
                update(AffiliateAsset)
                .where(
                    AffiliateAsset.campaign_id == campaign.id,
                    AffiliateAsset.membership_id.in_(
                        select(ProgramMembership.id).where(
                            ProgramMembership.status == MembershipStatus.ACTIVE,
                            ProgramMembership.program_id == campaign.program_id,
                        )
                    ),
                    exists(
                        select(CampaignParticipant.id).where(
                            CampaignParticipant.campaign_id == campaign.id,
                            CampaignParticipant.membership_id == AffiliateAsset.membership_id,
                            CampaignParticipant.status == CampaignParticipantStatus.SELECTED,
                        )
                    ),
                )
                .values(active=True)
            )
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="campaign.status_changed",
            entity_type="campaign",
            entity_id=campaign.id,
            data={"from": previous.value, "to": target.value},
            now=clock.now(),
        )
    return campaign


async def create_commission_plan(
    session: AsyncSession,
    principal: Principal,
    program_id: uuid.UUID,
    request: CommissionPlanCreateRequest,
) -> CommissionPlan:
    assert principal.brand_id is not None
    thresholds = [tier.threshold_gmv for tier in request.tiers]
    if thresholds != sorted(set(thresholds)):
        raise UnprocessableError(
            "invalid_tiers", "Tier thresholds must be unique and sorted in ascending order"
        )
    async with session.begin():
        await get_program_for_brand(session, program_id, principal.brand_id)
        if request.campaign_id:
            campaign = await session.scalar(
                select(Campaign).where(
                    Campaign.id == request.campaign_id,
                    Campaign.program_id == program_id,
                )
            )
            if campaign is None:
                raise NotFoundError(
                    "campaign_not_found", "Campaign does not belong to this program"
                )
        current_version = await session.scalar(
            select(func.coalesce(func.max(CommissionPlan.version), 0)).where(
                CommissionPlan.program_id == program_id,
                CommissionPlan.campaign_id == request.campaign_id,
            )
        )
        plan = CommissionPlan(
            program_id=program_id,
            campaign_id=request.campaign_id,
            version=int(current_version or 0) + 1,
            base_rate=request.base_rate,
            return_window_days=request.return_window_days,
            payout_minimum=request.payout_minimum,
            active_from=request.active_from,
        )
        session.add(plan)
        await session.flush()
        for tier in request.tiers:
            session.add(
                CommissionTier(
                    plan_id=plan.id,
                    threshold_gmv=tier.threshold_gmv,
                    rate=tier.rate,
                )
            )
        for bonus in request.bonuses:
            session.add(
                BonusRule(
                    plan_id=plan.id,
                    name=bonus.name,
                    metric=CommissionMetric(bonus.metric),
                    threshold=bonus.threshold,
                    amount=bonus.amount,
                )
            )
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="commission_plan.created",
            entity_type="commission_plan",
            entity_id=plan.id,
            data={"program_id": str(program_id), "version": plan.version},
            now=clock.now(),
        )
    return plan


async def active_plan_at(
    session: AsyncSession,
    *,
    program_id: uuid.UUID,
    campaign_id: uuid.UUID | None,
    occurred_at: datetime,
) -> CommissionPlan | None:
    if campaign_id:
        campaign_plan = await session.scalar(
            select(CommissionPlan)
            .where(
                CommissionPlan.program_id == program_id,
                CommissionPlan.campaign_id == campaign_id,
                CommissionPlan.active_from <= occurred_at,
            )
            .order_by(CommissionPlan.active_from.desc(), CommissionPlan.version.desc())
            .limit(1)
        )
        if campaign_plan:
            return campaign_plan
    return cast(
        CommissionPlan | None,
        await session.scalar(
            select(CommissionPlan)
            .where(
                CommissionPlan.program_id == program_id,
                CommissionPlan.campaign_id.is_(None),
                CommissionPlan.active_from <= occurred_at,
            )
            .order_by(CommissionPlan.active_from.desc(), CommissionPlan.version.desc())
            .limit(1)
        ),
    )
