import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.errors import ConflictError, NotFoundError, UnprocessableError
from creatorops.core.security import Principal
from creatorops.core.time import clock
from creatorops.models.enums import (
    ApplicationSource,
    ApplicationStatus,
    AssetType,
    MembershipStatus,
    ProgramStatus,
)
from creatorops.models.partnerships import (
    AffiliateAsset,
    CreatorApplication,
    ProgramMembership,
    TermsAcceptance,
)
from creatorops.models.programs import Program, ProgramTerms
from creatorops.schemas import ApplicationCreateRequest, ApplicationReviewRequest
from creatorops.services.shared import add_audit


async def apply_to_program(
    session: AsyncSession,
    principal: Principal,
    program_id: uuid.UUID,
    request: ApplicationCreateRequest,
) -> CreatorApplication:
    application = CreatorApplication(
        program_id=program_id,
        creator_id=principal.user_id,
        source=ApplicationSource.SELF,
        status=ApplicationStatus.SUBMITTED,
        motivation=request.motivation,
    )
    try:
        async with session.begin():
            program = await session.get(Program, program_id)
            if program is None or program.status != ProgramStatus.ACTIVE:
                raise NotFoundError("active_program_not_found", "An active program was not found")
            session.add(application)
            await session.flush()
            add_audit(
                session,
                brand_id=program.brand_id,
                actor_user_id=principal.user_id,
                action="creator.application_submitted",
                entity_type="creator_application",
                entity_id=application.id,
                data={"program_id": str(program_id)},
                now=clock.now(),
            )
    except IntegrityError as exc:
        raise ConflictError(
            "application_already_exists",
            "This creator already has an application for the program",
        ) from exc
    return application


async def list_applications(
    session: AsyncSession,
    brand_id: uuid.UUID,
    *,
    status: ApplicationStatus | None = None,
) -> list[CreatorApplication]:
    statement = (
        select(CreatorApplication)
        .join(Program, Program.id == CreatorApplication.program_id)
        .where(Program.brand_id == brand_id)
        .order_by(CreatorApplication.created_at.desc())
    )
    if status:
        statement = statement.where(CreatorApplication.status == status)
    return list((await session.scalars(statement)).all())


async def review_application(
    session: AsyncSession,
    principal: Principal,
    application_id: uuid.UUID,
    request: ApplicationReviewRequest,
) -> tuple[CreatorApplication, ProgramMembership | None]:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        row = (
            await session.execute(
                select(CreatorApplication, Program)
                .join(Program, Program.id == CreatorApplication.program_id)
                .where(
                    CreatorApplication.id == application_id,
                    Program.brand_id == principal.brand_id,
                )
                .with_for_update(of=CreatorApplication)
            )
        ).first()
        if row is None:
            raise NotFoundError("application_not_found", "Application was not found")
        application, program = row
        target = ApplicationStatus(request.decision)
        if application.status == target:
            existing_membership = await session.scalar(
                select(ProgramMembership).where(ProgramMembership.application_id == application.id)
            )
            return application, existing_membership
        allowed: dict[ApplicationStatus, set[ApplicationStatus]] = {
            ApplicationStatus.SUBMITTED: {
                ApplicationStatus.IN_REVIEW,
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
            },
            ApplicationStatus.IN_REVIEW: {
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
            },
        }
        if target not in allowed.get(application.status, set()):
            raise ConflictError(
                "invalid_application_transition",
                f"Cannot transition application from {application.status} to {target}",
            )
        application.status = target
        application.review_note = request.note
        application.reviewed_by = principal.user_id
        application.reviewed_at = now
        membership: ProgramMembership | None = None
        if target == ApplicationStatus.APPROVED:
            membership = ProgramMembership(
                program_id=application.program_id,
                creator_id=application.creator_id,
                application_id=application.id,
                status=MembershipStatus.AWAITING_TERMS,
            )
            session.add(membership)
            await session.flush()
        add_audit(
            session,
            brand_id=program.brand_id,
            actor_user_id=principal.user_id,
            action=f"creator.application_{target.value}",
            entity_type="creator_application",
            entity_id=application.id,
            data={"note": request.note},
            now=now,
        )
    return application, membership


async def accept_terms(
    session: AsyncSession,
    principal: Principal,
    membership_id: uuid.UUID,
    terms_id: uuid.UUID,
    *,
    ip_address: str | None,
    user_agent: str | None,
) -> tuple[ProgramMembership, list[AffiliateAsset]]:
    now = clock.now()
    async with session.begin():
        membership = await session.scalar(
            select(ProgramMembership)
            .where(
                ProgramMembership.id == membership_id,
                ProgramMembership.creator_id == principal.user_id,
            )
            .with_for_update()
        )
        if membership is None:
            raise NotFoundError("membership_not_found", "Creator membership was not found")
        terms = await session.scalar(
            select(ProgramTerms).where(
                ProgramTerms.id == terms_id,
                ProgramTerms.program_id == membership.program_id,
            )
        )
        if terms is None:
            raise NotFoundError("terms_not_found", "Terms do not belong to this program")
        latest_required = await session.scalar(
            select(ProgramTerms)
            .where(
                ProgramTerms.program_id == membership.program_id,
                ProgramTerms.required.is_(True),
            )
            .order_by(ProgramTerms.version.desc())
            .limit(1)
        )
        if latest_required and latest_required.id != terms.id:
            raise ConflictError("stale_terms", "The latest required terms must be accepted")
        existing = await session.scalar(
            select(TermsAcceptance).where(
                TermsAcceptance.membership_id == membership.id,
                TermsAcceptance.terms_id == terms.id,
            )
        )
        if existing is None:
            session.add(
                TermsAcceptance(
                    membership_id=membership.id,
                    terms_id=terms.id,
                    accepted_at=now,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            )
        if membership.status in {
            MembershipStatus.PAUSED,
            MembershipStatus.OFFBOARDED,
        }:
            raise ConflictError(
                "membership_not_activatable",
                f"A {membership.status.value} membership cannot accept terms to reactivate",
            )
        membership.status = MembershipStatus.ACTIVE
        membership.activated_at = now
        membership.version += 1

        assets = list(
            (
                await session.scalars(
                    select(AffiliateAsset).where(AffiliateAsset.membership_id == membership.id)
                )
            ).all()
        )
        if not assets:
            coupon = AffiliateAsset(
                membership_id=membership.id,
                asset_type=AssetType.COUPON,
                code=f"CO-{secrets.token_hex(4).upper()}",
                active=True,
            )
            link = AffiliateAsset(
                membership_id=membership.id,
                asset_type=AssetType.LINK,
                code=secrets.token_urlsafe(9),
                target_url="http://localhost:8000/docs",
                active=True,
            )
            session.add_all([coupon, link])
            await session.flush()
            assets = [coupon, link]
        else:
            for asset in assets:
                asset.active = True

        program = await session.get(Program, membership.program_id)
        if program is None:
            raise UnprocessableError("program_missing", "Membership has no valid program")
        add_audit(
            session,
            brand_id=program.brand_id,
            actor_user_id=principal.user_id,
            action="creator.terms_accepted",
            entity_type="program_membership",
            entity_id=membership.id,
            data={"terms_id": str(terms.id), "terms_version": terms.version},
            now=now,
        )
    return membership, assets


async def list_creator_memberships(
    session: AsyncSession, creator_id: uuid.UUID
) -> list[ProgramMembership]:
    return list(
        (
            await session.scalars(
                select(ProgramMembership)
                .where(ProgramMembership.creator_id == creator_id)
                .order_by(ProgramMembership.created_at.desc())
            )
        ).all()
    )


async def list_membership_assets(
    session: AsyncSession,
    *,
    membership_id: uuid.UUID,
    creator_id: uuid.UUID,
) -> list[AffiliateAsset]:
    owned = await session.scalar(
        select(ProgramMembership.id).where(
            ProgramMembership.id == membership_id,
            ProgramMembership.creator_id == creator_id,
        )
    )
    if owned is None:
        raise NotFoundError("membership_not_found", "Creator membership was not found")
    return list(
        (
            await session.scalars(
                select(AffiliateAsset)
                .where(AffiliateAsset.membership_id == membership_id)
                .order_by(AffiliateAsset.asset_type)
            )
        ).all()
    )


async def list_assets(
    session: AsyncSession, creator_id: uuid.UUID, membership_id: uuid.UUID
) -> list[AffiliateAsset]:
    membership = await session.scalar(
        select(ProgramMembership).where(
            ProgramMembership.id == membership_id,
            ProgramMembership.creator_id == creator_id,
        )
    )
    if membership is None:
        raise NotFoundError("membership_not_found", "Creator membership was not found")
    return list(
        (
            await session.scalars(
                select(AffiliateAsset)
                .where(AffiliateAsset.membership_id == membership_id)
                .order_by(AffiliateAsset.asset_type)
            )
        ).all()
    )
