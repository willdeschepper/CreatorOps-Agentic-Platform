import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, get_principal, require_creator, require_roles
from creatorops.core.time import clock
from creatorops.models.enums import (
    ApplicationStatus,
    BrandRole,
    CampaignParticipantStatus,
    InvitationStatus,
    LedgerBucket,
    MembershipStatus,
)
from creatorops.models.partnerships import (
    CampaignParticipant,
    CreatorApplication,
    ProgramMembership,
)
from creatorops.schemas import (
    ApplicationCreateRequest,
    ApplicationDetailResponse,
    ApplicationResponse,
    ApplicationReviewRequest,
    ApplicationReviewResponse,
    ApplicationWithdrawRequest,
    AssetResponse,
    BalanceResponse,
    CampaignParticipantDetailResponse,
    CampaignParticipantResponse,
    CampaignParticipantsRequest,
    CampaignParticipantStatusRequest,
    CreatorSummary,
    InvitationAcceptResponse,
    InvitationCreatedResponse,
    InvitationCreateRequest,
    InvitationInspectResponse,
    InvitationResponse,
    MembershipDetailResponse,
    MembershipResponse,
    MembershipStatusRequest,
    PageResponse,
    RejectRequest,
    SocialProfileResponse,
    TermsAcceptanceRequest,
    TermsAcceptanceResponse,
    TermsResponse,
)
from creatorops.services import commissions, partnerships

router = APIRouter(tags=["partnerships"])
partnership_staff = require_roles(BrandRole.OWNER, BrandRole.OPS)


async def _application_payload(
    session: AsyncSession, application: CreatorApplication
) -> ApplicationDetailResponse:
    row = application
    program, creator, socials = await partnerships.application_context(session, row)
    return ApplicationDetailResponse(
        **ApplicationResponse.model_validate(row).model_dump(),
        program_name=program.name,
        creator=CreatorSummary(
            id=creator.id,
            email=creator.email,
            display_name=creator.display_name,
            socials=[SocialProfileResponse.model_validate(item) for item in socials],
        ),
    )


async def _membership_payload(
    session: AsyncSession, membership: ProgramMembership
) -> MembershipDetailResponse:
    row = membership
    (
        program,
        creator,
        socials,
        required_terms,
        accepted_version,
        assets,
    ) = await partnerships.membership_context(session, row)
    balances = await commissions.balances_for_membership(session, row.id)
    return MembershipDetailResponse(
        **MembershipResponse.model_validate(row).model_dump(),
        program_name=program.name,
        creator=CreatorSummary(
            id=creator.id,
            email=creator.email,
            display_name=creator.display_name,
            socials=[SocialProfileResponse.model_validate(item) for item in socials],
        ),
        accepted_terms_version=accepted_version,
        required_terms=TermsResponse.model_validate(required_terms) if required_terms else None,
        assets=[AssetResponse.model_validate(asset) for asset in assets],
        balance=BalanceResponse(
            membership_id=row.id,
            pending=balances[LedgerBucket.PENDING],
            available=balances[LedgerBucket.AVAILABLE],
            reserved=balances[LedgerBucket.RESERVED],
            paid=balances[LedgerBucket.PAID],
        ),
    )


async def _participant_payload(
    session: AsyncSession, participant: CampaignParticipant
) -> CampaignParticipantDetailResponse:
    row = participant
    membership = await session.get(ProgramMembership, row.membership_id)
    if membership is None:
        raise RuntimeError("Campaign participant has no membership")
    (
        _program,
        creator,
        socials,
        _terms,
        _accepted,
        all_assets,
    ) = await partnerships.membership_context(session, membership)
    assets = [asset for asset in all_assets if asset.campaign_id == row.campaign_id]
    return CampaignParticipantDetailResponse(
        **CampaignParticipantResponse.model_validate(row).model_dump(),
        creator=CreatorSummary(
            id=creator.id,
            email=creator.email,
            display_name=creator.display_name,
            socials=[SocialProfileResponse.model_validate(item) for item in socials],
        ),
        assets=[AssetResponse.model_validate(asset) for asset in assets],
    )


@router.post(
    "/programs/{program_id}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply(
    program_id: uuid.UUID,
    body: ApplicationCreateRequest,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    row = await partnerships.apply_to_program(session, principal, program_id, body)
    return ApplicationResponse.model_validate(row)


@router.get("/applications", response_model=PageResponse[ApplicationDetailResponse])
async def applications(
    application_status: ApplicationStatus | None = None,
    program_id: uuid.UUID | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ApplicationDetailResponse]:
    assert principal.brand_id is not None
    rows, total = await partnerships.list_applications(
        session,
        principal.brand_id,
        status=application_status,
        program_id=program_id,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[await _application_payload(session, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/applications/me", response_model=PageResponse[ApplicationDetailResponse])
async def my_applications(
    application_status: ApplicationStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ApplicationDetailResponse]:
    rows, total = await partnerships.list_creator_applications(
        session,
        creator_id=principal.user_id,
        status=application_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[await _application_payload(session, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> ApplicationDetailResponse:
    row = await partnerships.get_application(
        session, principal=principal, application_id=application_id
    )
    return await _application_payload(session, row)


@router.post("/applications/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    application_id: uuid.UUID,
    body: ApplicationWithdrawRequest,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> ApplicationResponse:
    row = await partnerships.withdraw_application(
        session,
        principal=principal,
        application_id=application_id,
        comment=body.comment,
    )
    return ApplicationResponse.model_validate(row)


@router.post("/applications/{application_id}/review", response_model=ApplicationReviewResponse)
async def review_application(
    application_id: uuid.UUID,
    body: ApplicationReviewRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> ApplicationReviewResponse:
    application, membership = await partnerships.review_application(
        session, principal, application_id, body
    )
    return ApplicationReviewResponse(
        application=ApplicationResponse.model_validate(application),
        membership=MembershipResponse.model_validate(membership) if membership else None,
    )


@router.post(
    "/memberships/{membership_id}/terms-acceptances",
    response_model=TermsAcceptanceResponse,
)
async def accept_terms(
    membership_id: uuid.UUID,
    body: TermsAcceptanceRequest,
    request: Request,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> TermsAcceptanceResponse:
    membership, assets = await partnerships.accept_terms(
        session,
        principal,
        membership_id,
        body.terms_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return TermsAcceptanceResponse(
        membership=MembershipResponse.model_validate(membership),
        assets=[AssetResponse.model_validate(asset) for asset in assets],
    )


@router.get("/memberships/me", response_model=PageResponse[MembershipResponse])
async def my_memberships(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[MembershipResponse]:
    rows, total = await partnerships.list_creator_memberships(
        session, principal.user_id, limit=limit, offset=offset
    )
    return PageResponse(
        items=[MembershipResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/memberships/{membership_id}/assets", response_model=list[AssetResponse])
async def membership_assets(
    membership_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> list[AssetResponse]:
    rows = await partnerships.list_membership_assets(
        session, membership_id=membership_id, principal=principal
    )
    return [AssetResponse.model_validate(row) for row in rows]


@router.post(
    "/programs/{program_id}/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    program_id: uuid.UUID,
    body: InvitationCreateRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> InvitationCreatedResponse:
    invitation, token, acceptance_url = await partnerships.create_invitation(
        session, principal=principal, program_id=program_id, request=body
    )
    return InvitationCreatedResponse(
        **InvitationResponse.model_validate(invitation).model_dump(),
        token=token,
        acceptance_url=acceptance_url,
    )


@router.get(
    "/programs/{program_id}/invitations",
    response_model=PageResponse[InvitationResponse],
)
async def list_invitations(
    program_id: uuid.UUID,
    invitation_status: InvitationStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[InvitationResponse]:
    assert principal.brand_id is not None
    rows, total = await partnerships.list_invitations(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        status=invitation_status,
        limit=limit,
        offset=offset,
    )
    now = clock.now()
    items = []
    for row in rows:
        payload = InvitationResponse.model_validate(row)
        if payload.status == InvitationStatus.PENDING and payload.expires_at <= now:
            payload.status = InvitationStatus.EXPIRED
        items.append(payload)
    return PageResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/invitations/{token}", response_model=InvitationInspectResponse)
async def inspect_invitation(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> InvitationInspectResponse:
    invitation, program, brand = await partnerships.inspect_invitation(session, token=token)
    effective_status = invitation.status
    if effective_status == InvitationStatus.PENDING and invitation.expires_at <= clock.now():
        effective_status = InvitationStatus.EXPIRED
    return InvitationInspectResponse(
        program_id=program.id,
        program_name=program.name,
        brand_name=brand.name,
        email_hint=partnerships._masked_email(invitation.email),
        status=effective_status,
        expires_at=invitation.expires_at,
    )


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    token: str,
    principal: Principal = Depends(require_creator),
    session: AsyncSession = Depends(get_session),
) -> InvitationAcceptResponse:
    invitation, application, membership = await partnerships.accept_invitation(
        session, principal=principal, token=token
    )
    return InvitationAcceptResponse(
        invitation=InvitationResponse.model_validate(invitation),
        application=ApplicationResponse.model_validate(application),
        membership=MembershipResponse.model_validate(membership),
    )


@router.post("/invitations/{invitation_id}/revoke", response_model=InvitationResponse)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    body: RejectRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> InvitationResponse:
    row = await partnerships.revoke_invitation(
        session,
        principal=principal,
        invitation_id=invitation_id,
        comment=body.comment,
    )
    return InvitationResponse.model_validate(row)


@router.get(
    "/programs/{program_id}/memberships",
    response_model=PageResponse[MembershipDetailResponse],
)
async def list_program_memberships(
    program_id: uuid.UUID,
    membership_status: MembershipStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[MembershipDetailResponse]:
    assert principal.brand_id is not None
    rows, total = await partnerships.list_program_memberships(
        session,
        brand_id=principal.brand_id,
        program_id=program_id,
        status=membership_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[await _membership_payload(session, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/memberships/{membership_id}", response_model=MembershipDetailResponse)
async def get_membership(
    membership_id: uuid.UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_session),
) -> MembershipDetailResponse:
    row = await partnerships.get_membership(
        session, principal=principal, membership_id=membership_id
    )
    return await _membership_payload(session, row)


@router.post("/memberships/{membership_id}/status", response_model=MembershipResponse)
async def change_membership_status(
    membership_id: uuid.UUID,
    body: MembershipStatusRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> MembershipResponse:
    row = await partnerships.change_membership_status(
        session, principal=principal, membership_id=membership_id, request=body
    )
    return MembershipResponse.model_validate(row)


@router.post(
    "/campaigns/{campaign_id}/participants",
    response_model=list[CampaignParticipantResponse],
    status_code=status.HTTP_201_CREATED,
)
async def select_campaign_participants(
    campaign_id: uuid.UUID,
    body: CampaignParticipantsRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> list[CampaignParticipantResponse]:
    rows = await partnerships.select_campaign_participants(
        session,
        principal=principal,
        campaign_id=campaign_id,
        membership_ids=body.membership_ids,
    )
    return [CampaignParticipantResponse.model_validate(row) for row in rows]


@router.get(
    "/campaigns/{campaign_id}/participants",
    response_model=PageResponse[CampaignParticipantDetailResponse],
)
async def list_campaign_participants(
    campaign_id: uuid.UUID,
    participant_status: CampaignParticipantStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[CampaignParticipantDetailResponse]:
    assert principal.brand_id is not None
    rows, total = await partnerships.list_campaign_participants(
        session,
        brand_id=principal.brand_id,
        campaign_id=campaign_id,
        status=participant_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[await _participant_payload(session, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/campaigns/{campaign_id}/participants/{membership_id}/status",
    response_model=CampaignParticipantResponse,
)
async def change_campaign_participant_status(
    campaign_id: uuid.UUID,
    membership_id: uuid.UUID,
    body: CampaignParticipantStatusRequest,
    principal: Principal = Depends(partnership_staff),
    session: AsyncSession = Depends(get_session),
) -> CampaignParticipantResponse:
    row = await partnerships.change_campaign_participant_status(
        session,
        principal=principal,
        campaign_id=campaign_id,
        membership_id=membership_id,
        request=body,
    )
    return CampaignParticipantResponse.model_validate(row)
