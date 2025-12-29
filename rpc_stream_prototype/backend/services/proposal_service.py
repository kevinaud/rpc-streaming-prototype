"""Proposal service implementation.

Implements the ProposalService gRPC service for the approval workflow.
"""

from typing import TYPE_CHECKING

import betterproto
import grpclib
from grpclib.const import Status

from rpc_stream_prototype.backend.logging import get_logger
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionResponse,
  GetSessionResponse,
  ProposalServiceBase,
  Session,
  SubmitDecisionResponse,
  SubmitProposalResponse,
  SubscribeResponse,
)

if TYPE_CHECKING:
  from collections.abc import AsyncIterator

  from rpc_stream_prototype.backend.storage.session_store import SessionStore
  from rpc_stream_prototype.generated.proposal.v1 import (
    CreateSessionRequest,
    GetSessionRequest,
    SubmitDecisionRequest,
    SubmitProposalRequest,
    SubscribeRequest,
  )

logger = get_logger("services.proposal")


class ProposalService(ProposalServiceBase):
  """Implementation of the ProposalService gRPC service.

  This service handles all approval workflow operations including
  session management, proposal submission, and decision processing.
  """

  def __init__(self, store: SessionStore) -> None:
    """Initialize the service with dependencies.

    Args:
        store: The session store for data persistence and event broadcasting.
    """
    self._store = store

  async def create_session(
    self, create_session_request: CreateSessionRequest
  ) -> CreateSessionResponse:
    """Create a new approval session.

    Args:
        create_session_request: The request (empty).

    Returns:
        Response containing the created session with its ID.
    """
    session = await self._store.create_session()
    logger.info("Created session: %s", session.session_id)

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
    session = await self._store.get_session(session_id)

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
    if not await self._store.session_exists(session_id):
      logger.warning("Subscribe failed - session not found: %s", session_id)
      raise grpclib.GRPCError(
        Status.NOT_FOUND,
        f"Session not found: {session_id}",
      )

    logger.info("Client %s subscribing to session %s", client_id, session_id)

    # Use the store's watch_session which handles history + live streaming
    async for event in self._store.watch_session(session_id):
      yield SubscribeResponse(event=event)
      # Log based on event type using betterproto's oneof helper
      event_type, proposal = betterproto.which_one_of(event, "event")
      if proposal and hasattr(proposal, "proposal_id"):
        logger.debug(
          "Sent %s for %s to client %s",
          event_type,
          proposal.proposal_id,
          client_id,
        )

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

    # Create and store the proposal (also broadcasts the event)
    proposal = await self._store.add_proposal(session_id, text.strip())

    if proposal is None:
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

    return SubmitProposalResponse(proposal=proposal)

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

    # Update the proposal (also broadcasts the event)
    updated = await self._store.update_proposal(
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

    return SubmitDecisionResponse(proposal=updated)
