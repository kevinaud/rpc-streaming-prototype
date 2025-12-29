"""Approval service implementation."""

from typing import AsyncIterator

import grpclib
from grpclib.const import Status

# Import from your generated code
from rpc_stream_prototype.generated.approval.v1 import (
  ApprovalRequest,
  ApprovalServiceBase,
  CreateSessionRequest,
  GetSessionRequest,
  Session,
  SessionEvent,
  SubmitDecisionPayload,
  SubmitRequestPayload,
  SubscribeRequest,
)


class ApprovalService(ApprovalServiceBase):
  async def create_session(
    self, create_session_request: "CreateSessionRequest"
  ) -> "Session":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def get_session(self, get_session_request: "GetSessionRequest") -> "Session":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def subscribe(
    self, subscribe_request: "SubscribeRequest"
  ) -> AsyncIterator[SessionEvent]:
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")
    # The yield below is unreachable but keeps static type checkers happy
    yield SessionEvent()

  async def submit_request(
    self, submit_request_payload: "SubmitRequestPayload"
  ) -> "ApprovalRequest":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")

  async def submit_decision(
    self, submit_decision_payload: "SubmitDecisionPayload"
  ) -> "ApprovalRequest":
    raise grpclib.GRPCError(Status.UNIMPLEMENTED, "Not implemented yet")
