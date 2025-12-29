"""Main proposal submission loop for CLI."""

import asyncio
import uuid
from typing import TYPE_CHECKING

from rpc_stream_prototype.cli.ui.display import (
  display_decision_received,
  display_info,
  display_proposal_sent,
  display_waiting_state,
)
from rpc_stream_prototype.cli.ui.prompts import prompt_proposal_text
from rpc_stream_prototype.generated.proposal.v1 import (
  ProposalStatus,
  SubmitProposalRequest,
  SubscribeRequest,
)

if TYPE_CHECKING:
  from rpc_stream_prototype.generated.proposal.v1 import ProposalServiceStub


async def run_proposal_loop(stub: ProposalServiceStub, session_id: str) -> None:
  """Main proposal submission loop.

  Prompts for proposal text, submits to server, waits for decision via subscription,
  displays decision result, and loops until interrupted.

  Args:
    stub: Connected ProposalServiceStub instance.
    session_id: The session ID to submit proposals to.
  """
  client_id = str(uuid.uuid4())  # Unique identifier for this CLI instance

  display_info("Ready to submit proposals. Press Ctrl+C to exit.")

  while True:
    text = prompt_proposal_text()
    if not text.strip():
      display_info("Empty proposal skipped. Please enter some text.")
      continue

    # Submit the proposal
    response = await stub.submit_proposal(
      SubmitProposalRequest(session_id=session_id, text=text)
    )
    proposal = response.proposal
    display_proposal_sent(proposal.proposal_id, proposal.text)
    display_waiting_state()

    # Wait for decision via subscription
    try:
      decision_received = False
      async for response in stub.subscribe(
        SubscribeRequest(session_id=session_id, client_id=client_id)
      ):
        event = response.event
        # Check if this is a decision for our proposal
        if (
          event.proposal_updated
          and event.proposal_updated.proposal_id == proposal.proposal_id
        ):
          updated_proposal = event.proposal_updated
          # Only process if decision was made (not PENDING)
          if updated_proposal.status in (
            ProposalStatus.APPROVED,
            ProposalStatus.REJECTED,
          ):
            approved = updated_proposal.status == ProposalStatus.APPROVED
            display_decision_received(approved)
            decision_received = True
            break

      if not decision_received:
        # Stream ended without receiving decision - shouldn't happen normally
        display_info("Connection interrupted. Please check the server.")

    except asyncio.CancelledError:
      # Allow clean shutdown
      raise
    except Exception as e:
      display_info(f"Error waiting for decision: {e}")
