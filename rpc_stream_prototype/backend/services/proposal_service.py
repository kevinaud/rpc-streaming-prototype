"""Proposal service implementation.

Implements the ProposalService gRPC service for the approval workflow.
"""

from typing import TYPE_CHECKING

import grpclib
from grpclib.const import Status

from rpc_stream_prototype.backend.events.broadcaster import (
  EventType,
  SessionEvent,
)
from rpc_stream_prototype.backend.logging import get_logger
from rpc_stream_prototype.backend.models.domain import Proposal as DomainProposal
from rpc_stream_prototype.backend.models.domain import (
  ProposalStatus as DomainProposalStatus,
)
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionResponse,
  GetSessionResponse,
  Proposal,
  ProposalServiceBase,
  ProposalStatus,
  Session,
  SubmitDecisionResponse,
  SubmitProposalResponse,
  SubscribeResponse,
)
from rpc_stream_prototype.generated.proposal.v1 import (
  SessionEvent as ProtoSessionEvent,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator

  from rpc_stream_prototype.backend.events.broadcaster import EventBroadcaster
  from rpc_stream_prototype.backend.storage.repository import SessionRepository
  from rpc_stream_prototype.generated.proposal.v1 import (
    CreateSessionRequest,
    GetSessionRequest,
    SubmitDecisionRequest,
    SubmitProposalRequest,
    SubscribeRequest,
  )

logger = get_logger("services.proposal")


def _domain_status_to_proto(status: DomainProposalStatus) -> ProposalStatus:
  """Convert domain ProposalStatus to proto ProposalStatus."""
  mapping = {
    DomainProposalStatus.PENDING: ProposalStatus.PENDING,
    DomainProposalStatus.APPROVED: ProposalStatus.APPROVED,
    DomainProposalStatus.REJECTED: ProposalStatus.REJECTED,
  }
  return mapping.get(status, ProposalStatus.UNSPECIFIED)


def _domain_proposal_to_proto(proposal: DomainProposal) -> Proposal:
  """Convert domain Proposal to proto Proposal."""
  return Proposal(
    proposal_id=proposal.proposal_id,
    text=proposal.text,
    status=_domain_status_to_proto(proposal.status),
    created_at=proposal.created_at,
  )


class ProposalService(ProposalServiceBase):
  """Implementation of the ProposalService gRPC service.

  This service handles all approval workflow operations including
  session management, proposal submission, and decision processing.
  """

  def __init__(
    self,
    repository: SessionRepository,
    broadcaster: EventBroadcaster,
  ) -> None:
    """Initialize the service with dependencies.

    Args:
        repository: The session repository for data persistence.
        broadcaster: The event broadcaster for real-time updates.
    """
    self._repository = repository
    self._broadcaster = broadcaster

  async def create_session(
    self, create_session_request: CreateSessionRequest
  ) -> CreateSessionResponse:
    """Create a new approval session.

    Args:
        create_session_request: The request (empty).

    Returns:
        Response containing the created session with its ID.
    """
    session = await self._repository.create_session()
    logger.info("Created session: %s", session.session_id)
    logger.debug("Session details: created_at=%s", session.created_at)

    return CreateSessionResponse(session=Session(session_id=session.session_id))

  async def get_session(
    self, get_session_request: GetSessionRequest
  ) -> GetSessionResponse:
    """Get a session by ID.

    Args:
        get_session_request: Request containing the session ID.

    Returns:
        Response containing the session.

    Raises:
        GRPCError: NOT_FOUND if session doesn't exist.
    """
    session_id = get_session_request.session_id
    session = await self._repository.get_session(session_id)

    if session is None:
      logger.warning("Session not found: %s", session_id)
      raise grpclib.GRPCError(
        Status.NOT_FOUND,
        f"Session not found: {session_id}",
      )

    logger.debug("Retrieved session: %s", session_id)
    return GetSessionResponse(session=Session(session_id=session.session_id))

  async def subscribe(
    self, subscribe_request: SubscribeRequest
  ) -> AsyncIterator[SubscribeResponse]:
    """Subscribe to session events.

    First replays historical events (all existing proposals),
    then streams new events as they occur.

    Args:
        subscribe_request: Request containing session_id and client_id.

    Yields:
        SubscribeResponse containing session events.

    Raises:
        GRPCError: NOT_FOUND if session doesn't exist.
    """
    session_id = subscribe_request.session_id
    client_id = subscribe_request.client_id

    # Verify session exists
    session = await self._repository.get_session(session_id)
    if session is None:
      logger.warning("Subscribe failed - session not found: %s", session_id)
      raise grpclib.GRPCError(
        Status.NOT_FOUND,
        f"Session not found: {session_id}",
      )

    logger.info("Client %s subscribing to session %s", client_id, session_id)

    # Replay historical proposals
    for proposal in session.proposals:
      proto_proposal = _domain_proposal_to_proto(proposal)
      if proposal.status == DomainProposalStatus.PENDING:
        event = ProtoSessionEvent(proposal_created=proto_proposal)
      else:
        event = ProtoSessionEvent(proposal_updated=proto_proposal)
      yield SubscribeResponse(event=event)
      logger.debug(
        "Replayed proposal %s to client %s",
        proposal.proposal_id,
        client_id,
      )

    # Subscribe to live events
    queue = await self._broadcaster.subscribe(session_id)
    logger.debug("Client %s now receiving live events", client_id)

    try:
      while True:
        event = await queue.get()
        proto_proposal = _domain_proposal_to_proto(event.proposal)

        if event.event_type == EventType.PROPOSAL_CREATED:
          proto_event = ProtoSessionEvent(proposal_created=proto_proposal)
        else:
          proto_event = ProtoSessionEvent(proposal_updated=proto_proposal)

        yield SubscribeResponse(event=proto_event)
        logger.debug(
          "Sent event %s for proposal %s to client %s",
          event.event_type.value,
          event.proposal.proposal_id,
          client_id,
        )
    finally:
      await self._broadcaster.unsubscribe(session_id, queue)
      logger.info("Client %s unsubscribed from session %s", client_id, session_id)

  async def submit_proposal(
    self, submit_proposal_request: SubmitProposalRequest
  ) -> SubmitProposalResponse:
    """Submit a new proposal for approval.

    Args:
        submit_proposal_request: Request containing session_id and text.

    Returns:
        Response containing the created proposal.

    Raises:
        GRPCError: NOT_FOUND if session doesn't exist.
        GRPCError: INVALID_ARGUMENT if text is empty.
    """
    session_id = submit_proposal_request.session_id
    text = submit_proposal_request.text

    # Validate input
    if not text or not text.strip():
      logger.warning("Empty proposal text submitted to session %s", session_id)
      raise grpclib.GRPCError(
        Status.INVALID_ARGUMENT,
        "Proposal text cannot be empty",
      )

    # Create and store the proposal
    proposal = DomainProposal.create(session_id=session_id, text=text.strip())
    stored = await self._repository.add_proposal(session_id, proposal)

    if stored is None:
      logger.warning("Submit proposal failed - session not found: %s", session_id)
      raise grpclib.GRPCError(
        Status.NOT_FOUND,
        f"Session not found: {session_id}",
      )

    logger.info(
      "Proposal %s submitted to session %s",
      proposal.proposal_id,
      session_id,
    )

    # Broadcast the event
    event = SessionEvent(
      session_id=session_id,
      event_type=EventType.PROPOSAL_CREATED,
      proposal=proposal,
    )
    await self._broadcaster.broadcast(event)

    return SubmitProposalResponse(proposal=_domain_proposal_to_proto(proposal))

  async def submit_decision(
    self, submit_decision_request: SubmitDecisionRequest
  ) -> SubmitDecisionResponse:
    """Submit a decision on a proposal.

    Args:
        submit_decision_request: Request with session_id, proposal_id, approved.

    Returns:
        Response containing the updated proposal.

    Raises:
        GRPCError: NOT_FOUND if session or proposal doesn't exist.
    """
    session_id = submit_decision_request.session_id
    proposal_id = submit_decision_request.proposal_id
    approved = submit_decision_request.approved

    # Update the proposal
    updated = await self._repository.update_proposal(
      session_id,
      proposal_id,
      approved=approved,
    )

    if updated is None:
      logger.warning(
        "Submit decision failed - session %s or proposal %s not found",
        session_id,
        proposal_id,
      )
      raise grpclib.GRPCError(
        Status.NOT_FOUND,
        f"Session or proposal not found: {session_id}/{proposal_id}",
      )

    decision = "approved" if approved else "rejected"
    logger.info(
      "Proposal %s in session %s was %s",
      proposal_id,
      session_id,
      decision,
    )

    # Broadcast the event
    event = SessionEvent(
      session_id=session_id,
      event_type=EventType.PROPOSAL_UPDATED,
      proposal=updated,
    )
    await self._broadcaster.broadcast(event)

    return SubmitDecisionResponse(proposal=_domain_proposal_to_proto(updated))
