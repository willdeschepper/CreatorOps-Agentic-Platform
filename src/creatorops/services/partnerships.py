import secrets
import uuid
from datetime import timedelta
from typing import cast

from sqlalchemy import case, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.config import settings
from creatorops.core.errors import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from creatorops.core.security import Principal, stable_hash
from creatorops.core.time import clock
from creatorops.models.enums import (
    ApplicationSource,
    ApplicationStatus,
    AssetType,
    BrandRole,
    CampaignParticipantStatus,
    CampaignStatus,
    InvitationStatus,
    MembershipStatus,
    ProgramStatus,
)
from creatorops.models.identity import Brand, SocialProfile, User
from creatorops.models.partnerships import (
    AffiliateAsset,
    CampaignParticipant,
    CreatorApplication,
    CreatorInvitation,
    ProgramMembership,
    TermsAcceptance,
)
from creatorops.models.programs import Campaign, Program, ProgramTerms
from creatorops.schemas import (
    ApplicationCreateRequest,
    ApplicationReviewRequest,
    CampaignParticipantStatusRequest,
    InvitationCreateRequest,
    MembershipStatusRequest,
)
from creatorops.services.shared import add_audit, normalize_email


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
            membership_exists = await session.scalar(
                select(ProgramMembership.id).where(
                    ProgramMembership.program_id == program_id,
                    ProgramMembership.creator_id == principal.user_id,
                )
            )
            if membership_exists is not None:
                raise ConflictError(
                    "membership_already_exists", "This creator already belongs to the program"
                )
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
    program_id: uuid.UUID | None = None,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[CreatorApplication], int]:
    statement = (
        select(CreatorApplication)
        .join(Program, Program.id == CreatorApplication.program_id)
        .where(Program.brand_id == brand_id)
        .order_by(CreatorApplication.created_at.desc())
    )
    if status:
        statement = statement.where(CreatorApplication.status == status)
    if program_id:
        statement = statement.where(CreatorApplication.program_id == program_id)
    total_statement = (
        select(func.count())
        .select_from(CreatorApplication)
        .join(Program, Program.id == CreatorApplication.program_id)
        .where(Program.brand_id == brand_id)
    )
    if status:
        total_statement = total_statement.where(CreatorApplication.status == status)
    if program_id:
        total_statement = total_statement.where(CreatorApplication.program_id == program_id)
    total = int(await session.scalar(total_statement) or 0)
    rows = list(
        (
            await session.scalars(
                statement.order_by(
                    CreatorApplication.created_at.desc(), CreatorApplication.id.desc()
                )
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_creator_applications(
    session: AsyncSession,
    *,
    creator_id: uuid.UUID,
    status: ApplicationStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[CreatorApplication], int]:
    filters = [CreatorApplication.creator_id == creator_id]
    if status:
        filters.append(CreatorApplication.status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(CreatorApplication).where(*filters))
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(CreatorApplication)
                .where(*filters)
                .order_by(CreatorApplication.created_at.desc(), CreatorApplication.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_application(
    session: AsyncSession, *, principal: Principal, application_id: uuid.UUID
) -> CreatorApplication:
    statement = select(CreatorApplication).where(CreatorApplication.id == application_id)
    if principal.brand_id is None:
        statement = statement.where(CreatorApplication.creator_id == principal.user_id)
    else:
        if principal.role not in {BrandRole.OWNER, BrandRole.OPS}:
            raise ForbiddenError()
        statement = statement.join(Program, Program.id == CreatorApplication.program_id).where(
            Program.brand_id == principal.brand_id
        )
    application = await session.scalar(statement)
    if application is None:
        raise NotFoundError("application_not_found", "Application was not found")
    return application


async def withdraw_application(
    session: AsyncSession,
    *,
    principal: Principal,
    application_id: uuid.UUID,
    comment: str,
) -> CreatorApplication:
    now = clock.now()
    async with session.begin():
        application = await session.scalar(
            select(CreatorApplication)
            .where(
                CreatorApplication.id == application_id,
                CreatorApplication.creator_id == principal.user_id,
            )
            .with_for_update()
        )
        if application is None:
            raise NotFoundError("application_not_found", "Application was not found")
        if application.status == ApplicationStatus.WITHDRAWN:
            return application
        if application.status not in {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.IN_REVIEW,
        }:
            raise ConflictError(
                "application_not_withdrawable",
                f"A {application.status.value} application cannot be withdrawn",
            )
        application.status = ApplicationStatus.WITHDRAWN
        application.review_note = comment
        program = await session.get(Program, application.program_id)
        assert program is not None
        add_audit(
            session,
            brand_id=program.brand_id,
            actor_user_id=principal.user_id,
            action="creator.application_withdrawn",
            entity_type="creator_application",
            entity_id=application.id,
            data={"comment": comment},
            now=now,
        )
    return application


async def application_context(
    session: AsyncSession, application: CreatorApplication
) -> tuple[Program, User, list[SocialProfile]]:
    program = await session.get(Program, application.program_id)
    creator = await session.get(User, application.creator_id)
    if program is None or creator is None:
        raise UnprocessableError("application_context_missing", "Application context is missing")
    socials = list(
        (
            await session.scalars(
                select(SocialProfile)
                .where(SocialProfile.creator_id == creator.id)
                .order_by(SocialProfile.network)
            )
        ).all()
    )
    return program, creator, socials


def _masked_email(email: str) -> str:
    local, _, domain = email.partition("@")
    visible = local[:2]
    return f"{visible}{'*' * max(1, len(local) - len(visible))}@{domain}"


async def create_invitation(
    session: AsyncSession,
    *,
    principal: Principal,
    program_id: uuid.UUID,
    request: InvitationCreateRequest,
) -> tuple[CreatorInvitation, str, str]:
    assert principal.brand_id is not None
    now = clock.now()
    token = secrets.token_urlsafe(32)
    email = normalize_email(str(request.email))
    invitation = CreatorInvitation(
        program_id=program_id,
        created_by=principal.user_id,
        email=email,
        token_hash=stable_hash(token),
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=request.expires_in_hours),
    )
    async with session.begin():
        program = await session.scalar(
            select(Program).where(Program.id == program_id, Program.brand_id == principal.brand_id)
        )
        if program is None:
            raise NotFoundError("program_not_found", "Program was not found")
        existing_user = await session.scalar(select(User).where(User.email == email))
        if existing_user is not None:
            membership = await session.scalar(
                select(ProgramMembership.id).where(
                    ProgramMembership.program_id == program_id,
                    ProgramMembership.creator_id == existing_user.id,
                )
            )
            if membership is not None:
                raise ConflictError(
                    "membership_already_exists",
                    "The invited creator already belongs to the program",
                )
        session.add(invitation)
        await session.flush()
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="creator.invitation_created",
            entity_type="creator_invitation",
            entity_id=invitation.id,
            data={"program_id": str(program_id), "email": email},
            now=now,
        )
    return invitation, token, f"{settings.frontend_base_url}/invites/{token}"


async def list_invitations(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID,
    status: InvitationStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[CreatorInvitation], int]:
    program_exists = await session.scalar(
        select(Program.id).where(Program.id == program_id, Program.brand_id == brand_id)
    )
    if program_exists is None:
        raise NotFoundError("program_not_found", "Program was not found")
    filters = [CreatorInvitation.program_id == program_id]
    effective_status = case(
        (
            (CreatorInvitation.status == InvitationStatus.PENDING)
            & (CreatorInvitation.expires_at <= clock.now()),
            InvitationStatus.EXPIRED,
        ),
        else_=CreatorInvitation.status,
    )
    if status:
        filters.append(effective_status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(CreatorInvitation).where(*filters))
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(CreatorInvitation)
                .where(*filters)
                .order_by(CreatorInvitation.created_at.desc(), CreatorInvitation.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def inspect_invitation(
    session: AsyncSession, *, token: str
) -> tuple[CreatorInvitation, Program, Brand]:
    invitation = await session.scalar(
        select(CreatorInvitation).where(CreatorInvitation.token_hash == stable_hash(token))
    )
    if invitation is None:
        raise NotFoundError("invitation_not_found", "Invitation was not found")
    program = await session.get(Program, invitation.program_id)
    if program is None:
        raise NotFoundError("invitation_not_found", "Invitation was not found")
    brand = await session.get(Brand, program.brand_id)
    if brand is None:
        raise NotFoundError("invitation_not_found", "Invitation was not found")
    return invitation, program, brand


async def accept_invitation(
    session: AsyncSession, *, principal: Principal, token: str
) -> tuple[CreatorInvitation, CreatorApplication, ProgramMembership]:
    now = clock.now()
    async with session.begin():
        invitation = await session.scalar(
            select(CreatorInvitation)
            .where(CreatorInvitation.token_hash == stable_hash(token))
            .with_for_update()
        )
        if invitation is None:
            raise NotFoundError("invitation_not_found", "Invitation was not found")
        if invitation.status == InvitationStatus.ACCEPTED:
            if invitation.accepted_by != principal.user_id or invitation.application_id is None:
                raise ConflictError("invitation_already_used", "Invitation was already used")
            application = await session.get(CreatorApplication, invitation.application_id)
            membership = await session.scalar(
                select(ProgramMembership).where(
                    ProgramMembership.application_id == invitation.application_id
                )
            )
            if application is None or membership is None:
                raise UnprocessableError(
                    "invitation_result_missing", "Accepted invitation has incomplete state"
                )
            return invitation, application, membership
        if invitation.status == InvitationStatus.PENDING and invitation.expires_at <= now:
            raise ConflictError("invitation_not_usable", "Invitation is expired")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError("invitation_not_usable", f"Invitation is {invitation.status.value}")
        creator = await session.get(User, principal.user_id)
        if creator is None or normalize_email(creator.email) != invitation.email:
            raise ConflictError(
                "invitation_email_mismatch", "Invitation belongs to another email address"
            )
        existing_membership = await session.scalar(
            select(ProgramMembership).where(
                ProgramMembership.program_id == invitation.program_id,
                ProgramMembership.creator_id == principal.user_id,
            )
        )
        if existing_membership is not None:
            raise ConflictError(
                "membership_already_exists", "Creator already belongs to this program"
            )
        application = await session.scalar(
            select(CreatorApplication)
            .where(
                CreatorApplication.program_id == invitation.program_id,
                CreatorApplication.creator_id == principal.user_id,
                CreatorApplication.status.in_(
                    [ApplicationStatus.SUBMITTED, ApplicationStatus.IN_REVIEW]
                ),
            )
            .with_for_update()
        )
        if application is None:
            application = CreatorApplication(
                program_id=invitation.program_id,
                creator_id=principal.user_id,
                source=ApplicationSource.INVITE,
                status=ApplicationStatus.APPROVED,
                motivation="Accepted local invitation",
                reviewed_at=now,
            )
            session.add(application)
            await session.flush()
        else:
            application.status = ApplicationStatus.APPROVED
            application.source = ApplicationSource.INVITE
            application.reviewed_at = now
        membership = ProgramMembership(
            program_id=invitation.program_id,
            creator_id=principal.user_id,
            application_id=application.id,
            status=MembershipStatus.AWAITING_TERMS,
        )
        session.add(membership)
        await session.flush()
        invitation.status = InvitationStatus.ACCEPTED
        invitation.used_at = now
        invitation.accepted_by = principal.user_id
        invitation.application_id = application.id
        program = await session.get(Program, invitation.program_id)
        assert program is not None
        add_audit(
            session,
            brand_id=program.brand_id,
            actor_user_id=principal.user_id,
            action="creator.invitation_accepted",
            entity_type="creator_invitation",
            entity_id=invitation.id,
            data={"application_id": str(application.id), "membership_id": str(membership.id)},
            now=now,
        )
    return invitation, application, membership


async def revoke_invitation(
    session: AsyncSession,
    *,
    principal: Principal,
    invitation_id: uuid.UUID,
    comment: str,
) -> CreatorInvitation:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        invitation = await session.scalar(
            select(CreatorInvitation)
            .join(Program, Program.id == CreatorInvitation.program_id)
            .where(
                CreatorInvitation.id == invitation_id,
                Program.brand_id == principal.brand_id,
            )
            .with_for_update(of=CreatorInvitation)
        )
        if invitation is None:
            raise NotFoundError("invitation_not_found", "Invitation was not found")
        if invitation.status == InvitationStatus.REVOKED:
            return invitation
        if invitation.status == InvitationStatus.PENDING and invitation.expires_at <= now:
            raise ConflictError("invitation_not_revocable", "Invitation is expired")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError(
                "invitation_not_revocable", f"Invitation is {invitation.status.value}"
            )
        invitation.status = InvitationStatus.REVOKED
        invitation.revoked_at = now
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="creator.invitation_revoked",
            entity_type="creator_invitation",
            entity_id=invitation.id,
            data={"comment": comment},
            now=now,
        )
    return invitation


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

        program = await session.get(Program, membership.program_id)
        if program is None:
            raise UnprocessableError("program_missing", "Membership has no valid program")
        assets = list(
            (
                await session.scalars(
                    select(AffiliateAsset).where(AffiliateAsset.membership_id == membership.id)
                )
            ).all()
        )
        existing_program_types = {asset.asset_type for asset in assets if asset.campaign_id is None}
        if AssetType.COUPON not in existing_program_types:
            coupon = AffiliateAsset(
                membership_id=membership.id,
                asset_type=AssetType.COUPON,
                code=f"CO-{secrets.token_hex(4).upper()}",
                active=program.status == ProgramStatus.ACTIVE,
            )
            session.add(coupon)
            assets.append(coupon)
        if AssetType.LINK not in existing_program_types:
            link = AffiliateAsset(
                membership_id=membership.id,
                asset_type=AssetType.LINK,
                code=secrets.token_urlsafe(9),
                target_url=f"{settings.frontend_base_url}/programs/{program.slug}",
                active=program.status == ProgramStatus.ACTIVE,
            )
            session.add(link)
            assets.append(link)
        for asset in assets:
            if asset.campaign_id is None:
                asset.active = program.status == ProgramStatus.ACTIVE
                continue
            eligible_campaign = await session.scalar(
                select(Campaign.id)
                .join(
                    CampaignParticipant,
                    CampaignParticipant.campaign_id == Campaign.id,
                )
                .where(
                    Campaign.id == asset.campaign_id,
                    Campaign.status == CampaignStatus.ACTIVE,
                    CampaignParticipant.membership_id == membership.id,
                    CampaignParticipant.status == CampaignParticipantStatus.SELECTED,
                )
            )
            asset.active = program.status == ProgramStatus.ACTIVE and eligible_campaign is not None
        await session.flush()
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
    session: AsyncSession,
    creator_id: uuid.UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[ProgramMembership], int]:
    filters = [ProgramMembership.creator_id == creator_id]
    total = int(
        await session.scalar(select(func.count()).select_from(ProgramMembership).where(*filters))
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(ProgramMembership)
                .where(*filters)
                .order_by(ProgramMembership.created_at.desc(), ProgramMembership.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def list_membership_assets(
    session: AsyncSession,
    *,
    membership_id: uuid.UUID,
    principal: Principal,
) -> list[AffiliateAsset]:
    statement = select(ProgramMembership.id).where(ProgramMembership.id == membership_id)
    if principal.brand_id is None:
        statement = statement.where(ProgramMembership.creator_id == principal.user_id)
    else:
        statement = statement.join(Program, Program.id == ProgramMembership.program_id).where(
            Program.brand_id == principal.brand_id
        )
    owned = await session.scalar(statement)
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


async def list_program_memberships(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    program_id: uuid.UUID,
    status: MembershipStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[ProgramMembership], int]:
    program = await session.scalar(
        select(Program.id).where(Program.id == program_id, Program.brand_id == brand_id)
    )
    if program is None:
        raise NotFoundError("program_not_found", "Program was not found")
    filters = [ProgramMembership.program_id == program_id]
    if status:
        filters.append(ProgramMembership.status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(ProgramMembership).where(*filters))
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(ProgramMembership)
                .where(*filters)
                .order_by(ProgramMembership.created_at.desc(), ProgramMembership.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def get_membership(
    session: AsyncSession, *, principal: Principal, membership_id: uuid.UUID
) -> ProgramMembership:
    statement = select(ProgramMembership).where(ProgramMembership.id == membership_id)
    if principal.brand_id is None:
        statement = statement.where(ProgramMembership.creator_id == principal.user_id)
    else:
        statement = statement.join(Program, Program.id == ProgramMembership.program_id).where(
            Program.brand_id == principal.brand_id
        )
    membership = await session.scalar(statement)
    if membership is None:
        raise NotFoundError("membership_not_found", "Membership was not found")
    return membership


async def membership_context(
    session: AsyncSession, membership: ProgramMembership
) -> tuple[
    Program, User, list[SocialProfile], ProgramTerms | None, int | None, list[AffiliateAsset]
]:
    program = await session.get(Program, membership.program_id)
    creator = await session.get(User, membership.creator_id)
    if program is None or creator is None:
        raise UnprocessableError("membership_context_missing", "Membership context is missing")
    socials = list(
        (
            await session.scalars(
                select(SocialProfile)
                .where(SocialProfile.creator_id == creator.id)
                .order_by(SocialProfile.network)
            )
        ).all()
    )
    required_terms = await session.scalar(
        select(ProgramTerms)
        .where(ProgramTerms.program_id == program.id, ProgramTerms.required.is_(True))
        .order_by(ProgramTerms.version.desc())
        .limit(1)
    )
    accepted_version = await session.scalar(
        select(func.max(ProgramTerms.version))
        .join(TermsAcceptance, TermsAcceptance.terms_id == ProgramTerms.id)
        .where(TermsAcceptance.membership_id == membership.id)
    )
    assets = list(
        (
            await session.scalars(
                select(AffiliateAsset)
                .where(AffiliateAsset.membership_id == membership.id)
                .order_by(AffiliateAsset.campaign_id.nullsfirst(), AffiliateAsset.asset_type)
            )
        ).all()
    )
    return (
        program,
        creator,
        socials,
        required_terms,
        int(accepted_version) if accepted_version else None,
        assets,
    )


async def change_membership_status(
    session: AsyncSession,
    *,
    principal: Principal,
    membership_id: uuid.UUID,
    request: MembershipStatusRequest,
) -> ProgramMembership:
    assert principal.brand_id is not None
    target = MembershipStatus(request.status)
    now = clock.now()
    async with session.begin():
        membership = await session.scalar(
            select(ProgramMembership)
            .join(Program, Program.id == ProgramMembership.program_id)
            .where(
                ProgramMembership.id == membership_id,
                Program.brand_id == principal.brand_id,
            )
            .with_for_update(of=ProgramMembership)
        )
        if membership is None:
            raise NotFoundError("membership_not_found", "Membership was not found")
        if membership.status == target:
            return membership
        allowed = {
            MembershipStatus.AWAITING_TERMS: {MembershipStatus.OFFBOARDED},
            MembershipStatus.ACTIVE: {MembershipStatus.PAUSED, MembershipStatus.OFFBOARDED},
            MembershipStatus.PAUSED: {MembershipStatus.ACTIVE, MembershipStatus.OFFBOARDED},
        }
        if target not in allowed.get(membership.status, set()):
            raise ConflictError(
                "invalid_membership_transition",
                f"Cannot transition membership from {membership.status.value} to {target.value}",
            )
        program = await session.get(Program, membership.program_id)
        assert program is not None
        if target == MembershipStatus.ACTIVE:
            if program.status != ProgramStatus.ACTIVE:
                raise ConflictError("program_inactive", "Program must be active")
            required_terms = await session.scalar(
                select(ProgramTerms)
                .where(ProgramTerms.program_id == program.id, ProgramTerms.required.is_(True))
                .order_by(ProgramTerms.version.desc())
                .limit(1)
            )
            accepted = (
                await session.scalar(
                    select(TermsAcceptance.id).where(
                        TermsAcceptance.membership_id == membership.id,
                        TermsAcceptance.terms_id == required_terms.id,
                    )
                )
                if required_terms
                else None
            )
            if required_terms and accepted is None:
                raise ConflictError("terms_required", "Latest required terms were not accepted")
            membership.paused_at = None
            membership.activated_at = now
        elif target == MembershipStatus.PAUSED:
            membership.paused_at = now
        membership.status = target
        membership.version += 1
        if target != MembershipStatus.ACTIVE:
            await session.execute(
                update(AffiliateAsset)
                .where(AffiliateAsset.membership_id == membership.id)
                .values(active=False)
            )
        else:
            assets = list(
                (
                    await session.scalars(
                        select(AffiliateAsset).where(AffiliateAsset.membership_id == membership.id)
                    )
                ).all()
            )
            for asset in assets:
                if asset.campaign_id is None:
                    asset.active = True
                    continue
                participant = await session.scalar(
                    select(CampaignParticipant.id)
                    .join(Campaign, Campaign.id == CampaignParticipant.campaign_id)
                    .where(
                        CampaignParticipant.campaign_id == asset.campaign_id,
                        CampaignParticipant.membership_id == membership.id,
                        CampaignParticipant.status == CampaignParticipantStatus.SELECTED,
                        Campaign.status == CampaignStatus.ACTIVE,
                    )
                )
                asset.active = participant is not None
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="creator.membership_status_changed",
            entity_type="program_membership",
            entity_id=membership.id,
            data={"to": target.value, "comment": request.comment},
            now=now,
        )
    return membership


async def _upsert_campaign_asset(
    session: AsyncSession,
    *,
    membership_id: uuid.UUID,
    campaign_id: uuid.UUID,
    asset_type: AssetType,
    active: bool,
) -> AffiliateAsset:
    code = (
        f"CA-{secrets.token_hex(5).upper()}"
        if asset_type == AssetType.COUPON
        else secrets.token_urlsafe(12)
    )
    result = await session.execute(
        pg_insert(AffiliateAsset)
        .values(
            id=uuid.uuid4(),
            membership_id=membership_id,
            campaign_id=campaign_id,
            asset_type=asset_type,
            code=code,
            target_url=(
                f"{settings.frontend_base_url}/campaigns/{campaign_id}"
                if asset_type == AssetType.LINK
                else None
            ),
            active=active,
        )
        .on_conflict_do_update(
            index_elements=["membership_id", "campaign_id", "asset_type"],
            index_where=AffiliateAsset.campaign_id.is_not(None),
            set_={"active": active},
        )
        .returning(AffiliateAsset.id)
    )
    asset = await session.get(AffiliateAsset, result.scalar_one())
    assert asset is not None
    return asset


async def select_campaign_participants(
    session: AsyncSession,
    *,
    principal: Principal,
    campaign_id: uuid.UUID,
    membership_ids: list[uuid.UUID],
) -> list[CampaignParticipant]:
    assert principal.brand_id is not None
    now = clock.now()
    participants: list[CampaignParticipant] = []
    async with session.begin():
        row = (
            await session.execute(
                select(Campaign, Program)
                .join(Program, Program.id == Campaign.program_id)
                .where(Campaign.id == campaign_id, Program.brand_id == principal.brand_id)
                .with_for_update(of=Campaign)
            )
        ).first()
        if row is None:
            raise NotFoundError("campaign_not_found", "Campaign was not found")
        campaign, program = row
        if campaign.status in {CampaignStatus.ENDED, CampaignStatus.CANCELLED}:
            raise ConflictError("campaign_closed", "Closed campaigns cannot select creators")
        memberships = list(
            (
                await session.scalars(
                    select(ProgramMembership)
                    .where(
                        ProgramMembership.id.in_(membership_ids),
                        ProgramMembership.program_id == campaign.program_id,
                        ProgramMembership.status == MembershipStatus.ACTIVE,
                    )
                    .with_for_update()
                )
            ).all()
        )
        if {row.id for row in memberships} != set(membership_ids):
            raise UnprocessableError(
                "invalid_campaign_membership",
                "Every selected creator must be active in the campaign program",
            )
        for membership in memberships:
            existing_participant = await session.scalar(
                select(CampaignParticipant).where(
                    CampaignParticipant.campaign_id == campaign.id,
                    CampaignParticipant.membership_id == membership.id,
                )
            )
            if (
                existing_participant is not None
                and existing_participant.status == CampaignParticipantStatus.SELECTED
            ):
                participants.append(existing_participant)
                continue
            result = await session.execute(
                pg_insert(CampaignParticipant)
                .values(
                    id=uuid.uuid4(),
                    campaign_id=campaign.id,
                    membership_id=membership.id,
                    status=CampaignParticipantStatus.SELECTED,
                    selected_by=principal.user_id,
                    selected_at=now,
                    version=1,
                )
                .on_conflict_do_update(
                    constraint="uq_campaign_participant",
                    set_={
                        "status": CampaignParticipantStatus.SELECTED,
                        "removed_at": None,
                        "selected_by": principal.user_id,
                        "selected_at": case(
                            (
                                CampaignParticipant.status == CampaignParticipantStatus.REMOVED,
                                now,
                            ),
                            else_=CampaignParticipant.selected_at,
                        ),
                        "version": case(
                            (
                                CampaignParticipant.status == CampaignParticipantStatus.REMOVED,
                                CampaignParticipant.version + 1,
                            ),
                            else_=CampaignParticipant.version,
                        ),
                    },
                )
                .returning(CampaignParticipant.id)
            )
            participant = await session.get(CampaignParticipant, result.scalar_one())
            assert participant is not None
            participants.append(participant)
            active = (
                program.status == ProgramStatus.ACTIVE and campaign.status == CampaignStatus.ACTIVE
            )
            await _upsert_campaign_asset(
                session,
                membership_id=membership.id,
                campaign_id=campaign.id,
                asset_type=AssetType.COUPON,
                active=active,
            )
            await _upsert_campaign_asset(
                session,
                membership_id=membership.id,
                campaign_id=campaign.id,
                asset_type=AssetType.LINK,
                active=active,
            )
            add_audit(
                session,
                brand_id=principal.brand_id,
                actor_user_id=principal.user_id,
                action="campaign.creator_selected",
                entity_type="campaign_participant",
                entity_id=participant.id,
                data={"campaign_id": str(campaign.id), "membership_id": str(membership.id)},
                now=now,
            )
    return participants


async def list_campaign_participants(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    campaign_id: uuid.UUID,
    status: CampaignParticipantStatus | None,
    limit: int,
    offset: int,
) -> tuple[list[CampaignParticipant], int]:
    campaign = await session.scalar(
        select(Campaign.id)
        .join(Program, Program.id == Campaign.program_id)
        .where(Campaign.id == campaign_id, Program.brand_id == brand_id)
    )
    if campaign is None:
        raise NotFoundError("campaign_not_found", "Campaign was not found")
    filters = [CampaignParticipant.campaign_id == campaign_id]
    if status:
        filters.append(CampaignParticipant.status == status)
    total = int(
        await session.scalar(select(func.count()).select_from(CampaignParticipant).where(*filters))
        or 0
    )
    rows = list(
        (
            await session.scalars(
                select(CampaignParticipant)
                .where(*filters)
                .order_by(CampaignParticipant.selected_at.desc(), CampaignParticipant.id.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return rows, total


async def change_campaign_participant_status(
    session: AsyncSession,
    *,
    principal: Principal,
    campaign_id: uuid.UUID,
    membership_id: uuid.UUID,
    request: CampaignParticipantStatusRequest,
) -> CampaignParticipant:
    assert principal.brand_id is not None
    now = clock.now()
    async with session.begin():
        row = (
            await session.execute(
                select(CampaignParticipant, Campaign, Program, ProgramMembership)
                .join(Campaign, Campaign.id == CampaignParticipant.campaign_id)
                .join(Program, Program.id == Campaign.program_id)
                .join(
                    ProgramMembership,
                    ProgramMembership.id == CampaignParticipant.membership_id,
                )
                .where(
                    CampaignParticipant.campaign_id == campaign_id,
                    CampaignParticipant.membership_id == membership_id,
                    Program.brand_id == principal.brand_id,
                )
                .with_for_update(of=CampaignParticipant)
            )
        ).first()
        if row is None:
            raise NotFoundError("campaign_participant_not_found", "Participant was not found")
        participant = cast(CampaignParticipant, row[0])
        campaign = cast(Campaign, row[1])
        program = cast(Program, row[2])
        membership = cast(ProgramMembership, row[3])
        target = request.status
        if participant.status == target:
            return participant
        if target == CampaignParticipantStatus.SELECTED:
            if campaign.status in {CampaignStatus.ENDED, CampaignStatus.CANCELLED}:
                raise ConflictError("campaign_closed", "Closed campaigns cannot add creators")
            if membership.status != MembershipStatus.ACTIVE:
                raise ConflictError("membership_inactive", "Creator membership must be active")
            participant.selected_at = now
            participant.selected_by = principal.user_id
            participant.removed_at = None
        else:
            participant.removed_at = now
        participant.status = target
        participant.version += 1
        active = (
            target == CampaignParticipantStatus.SELECTED
            and program.status == ProgramStatus.ACTIVE
            and campaign.status == CampaignStatus.ACTIVE
            and membership.status == MembershipStatus.ACTIVE
        )
        await session.execute(
            update(AffiliateAsset)
            .where(
                AffiliateAsset.campaign_id == campaign_id,
                AffiliateAsset.membership_id == membership_id,
            )
            .values(active=active)
        )
        add_audit(
            session,
            brand_id=principal.brand_id,
            actor_user_id=principal.user_id,
            action="campaign.participant_status_changed",
            entity_type="campaign_participant",
            entity_id=participant.id,
            data={"to": target.value, "comment": request.comment},
            now=now,
        )
    return participant
