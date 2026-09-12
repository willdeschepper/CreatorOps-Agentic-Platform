import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from creatorops.core.db import get_session
from creatorops.core.security import Principal, require_roles
from creatorops.models.enums import BrandRole, FindingState
from creatorops.schemas import (
    ApprovalRequest,
    FindingResponse,
    GateRunResponse,
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


@router.get("/agent/findings", response_model=list[FindingResponse])
async def findings(
    finding_state: FindingState | None = None,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> list[FindingResponse]:
    assert principal.brand_id is not None
    rows = await agent_control.list_findings(
        session, brand_id=principal.brand_id, state=finding_state
    )
    return [FindingResponse.model_validate(row) for row in rows]


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


@router.post("/agent/proposals/{proposal_id}/gate")
async def gate(
    proposal_id: uuid.UUID,
    principal: Principal = Depends(finance_roles),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    assert principal.brand_id is not None
    proposal, run = await agent_control.gate_proposal(
        session, brand_id=principal.brand_id, proposal_id=proposal_id
    )
    return {
        "proposal": ProposalResponse.model_validate(proposal),
        "gate": GateRunResponse.model_validate(run),
    }


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
