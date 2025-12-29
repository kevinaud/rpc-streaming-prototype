"""Proposal service implementation."""

from typing import AsyncIterator

import grpclib
from grpclib.const import Status

# Import from your generated code
from rpc_stream_prototype.generated.proposal.v1 import (
  CreateSessionRequest,
  CreateSessionResponse,
  GetSessionRequest,
  GetSessionResponse,
  ProposalServiceBase,
  SessionEvent,
  SubmitDecisionRequest,
  SubmitDecisionResponse,
  SubmitProposalRequest,
  SubmitProposalResponse,
  SubscribeRequest,
  SubscribeResponse,
)


class ProposalService(ProposalServiceBase):
  async def create_session(
    self, create_session_request: "CreateSessionRequest"
  ) -> "CreateSessionResponse":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def get_session(
    self, get_session_request: "GetSessionRequest"
  ) -> "GetSessionResponse":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def subscribe(
    self, subscribe_request: "SubscribeRequest"
  ) -> AsyncIterator[SubscribeResponse]:
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")
    # The yield below is unreachable but keeps static type checkers happy
    yield SubscribeResponse(event=SessionEvent())

  async def submit_proposal(
    self, submit_proposal_request: "SubmitProposalRequest"
  ) -> "SubmitProposalResponse":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def submit_decision(
    self, submit_decision_request: "SubmitDecisionRequest"
  ) -> "SubmitDecisionResponse":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")
