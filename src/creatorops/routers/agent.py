import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import (
    BrandRole,
    FindingState,
    FindingType,
    ProposalState,
    ReconciliationRunStatus,
)
from creatorops.schemas import (
    ApprovalRequest,
    FindingDismissRequest,
    FindingResponse,
    GateResponse,
    GateRunResponse,
    PageResponse,
    ProposalDetailResponse,
    ProposalResponse,
    ReconciliationRunResponse,
    RejectRequest,
)
from creatorops.services import agent_control

router = APIRouter(tags=["agent-control"])
finance_roles = require_roles(BrandRole.OWNER, BrandRole.FINANCE)


@router.post(
    "/reconciliation/runs",
    response_model=ReconciliationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reconcile(
    principal: Principal = Depends(finance_roles),
) -> ReconciliationRunResponse:
    assert principal.brand_id is not None
    run, _findings = await agent_control.run_reconciliation(
        brand_id=principal.brand_id, started_by=principal.user_id
    )
    return ReconciliationRunResponse.model_validate(run)


@router.get("/reconciliation/runs", response_model=PageResponse[ReconciliationRunResponse])
async def list_reconciliation_runs(
    run_status: ReconciliationRunStatus | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ReconciliationRunResponse]:
    assert principal.brand_id is not None
    rows, total = await agent_control.list_reconciliation_runs(
        session,
        brand_id=principal.brand_id,
        status=run_status,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[ReconciliationRunResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/reconciliation/runs/{run_id}", response_model=ReconciliationRunResponse)
async def get_reconciliation_run(
    run_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ReconciliationRunResponse:
    assert principal.brand_id is not None
    row = await agent_control.get_reconciliation_run(
        session, brand_id=principal.brand_id, run_id=run_id
    )
    return ReconciliationRunResponse.model_validate(row)


@router.get("/agent/findings", response_model=PageResponse[FindingResponse])
async def findings(
    finding_state: FindingState | None = None,
    finding_type: FindingType | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[FindingResponse]:
    assert principal.brand_id is not None
    rows, total = await agent_control.list_findings(
        session,
        brand_id=principal.brand_id,
        state=finding_state,
        finding_type=finding_type,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[FindingResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/agent/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    assert principal.brand_id is not None
    row = await agent_control.get_finding(
        session, brand_id=principal.brand_id, finding_id=finding_id
    )
    return FindingResponse.model_validate(row)


@router.post("/agent/findings/{finding_id}/dismiss", response_model=FindingResponse)
async def dismiss_finding(
    finding_id: uuid.UUID,
    body: FindingDismissRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> FindingResponse:
    row = await agent_control.dismiss_finding(
        session, principal=principal, finding_id=finding_id, comment=body.comment
    )
    return FindingResponse.model_validate(row)


@router.post(
    "/agent/findings/{finding_id}/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def propose(
    finding_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ProposalResponse:
    assert principal.brand_id is not None
    proposal = await agent_control.generate_proposal(
        session, brand_id=principal.brand_id, finding_id=finding_id
    )
    return ProposalResponse.model_validate(proposal)


@router.get("/agent/proposals", response_model=PageResponse[ProposalResponse])
async def list_proposals(
    proposal_state: ProposalState | None = None,
    finding_id: uuid.UUID | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> PageResponse[ProposalResponse]:
    assert principal.brand_id is not None
    rows, total = await agent_control.list_proposals(
        session,
        brand_id=principal.brand_id,
        state=proposal_state,
        finding_id=finding_id,
        limit=limit,
        offset=offset,
    )
    return PageResponse(
        items=[ProposalResponse.model_validate(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/agent/proposals/{proposal_id}", response_model=ProposalDetailResponse)
async def get_proposal(
    proposal_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ProposalDetailResponse:
    assert principal.brand_id is not None
    proposal, gates = await agent_control.get_proposal_detail(
        session, brand_id=principal.brand_id, proposal_id=proposal_id
    )
    return ProposalDetailResponse(
        **ProposalResponse.model_validate(proposal).model_dump(),
        evidence_hash=proposal.evidence_hash,
        created_at=proposal.created_at,
        approved_by=proposal.approved_by,
        approval_comment=proposal.approval_comment,
        approved_at=proposal.approved_at,
        rejected_by=proposal.rejected_by,
        rejection_comment=proposal.rejection_comment,
        rejected_at=proposal.rejected_at,
        executed_at=proposal.executed_at,
        gates=[GateRunResponse.model_validate(row) for row in gates],
    )


@router.post("/agent/proposals/{proposal_id}/gate", response_model=GateResponse)
async def gate(
    proposal_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> GateResponse:
    assert principal.brand_id is not None
    proposal, run = await agent_control.gate_proposal(
        session, brand_id=principal.brand_id, proposal_id=proposal_id
    )
    return GateResponse(
        proposal=ProposalResponse.model_validate(proposal),
        gate=GateRunResponse.model_validate(run),
    )


@router.post("/agent/proposals/{proposal_id}/approve", response_model=ProposalResponse)
async def approve(
    proposal_id: uuid.UUID,
    body: ApprovalRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ProposalResponse:
    proposal = await agent_control.approve_proposal(
        session, principal=principal, proposal_id=proposal_id, comment=body.comment
    )
    return ProposalResponse.model_validate(proposal)


@router.post("/agent/proposals/{proposal_id}/reject", response_model=ProposalResponse)
async def reject(
    proposal_id: uuid.UUID,
    body: RejectRequest,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ProposalResponse:
    proposal = await agent_control.reject_proposal(
        session, principal=principal, proposal_id=proposal_id, comment=body.comment
    )
    return ProposalResponse.model_validate(proposal)


@router.post("/agent/proposals/{proposal_id}/execute", response_model=ProposalResponse)
async def execute(
    proposal_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> ProposalResponse:
    proposal = await agent_control.execute_proposal(
        session, principal=principal, proposal_id=proposal_id
    )
    return ProposalResponse.model_validate(proposal)
