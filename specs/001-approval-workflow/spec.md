# Feature Specification: Real-Time Approval Workflow

**Feature Branch**: `001-approval-workflow`  
**Created**: 2025-12-28  
**Status**: Draft  
**Input**: User description: Real-time Approval Workflow prototype with Coordination Service, Approver CLI, and Requester Web UI

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approver Starts Session (Priority: P1)

As an Approver, I want to start a new approval session from the CLI so that I can generate a Session ID to share with Requesters.

**Why this priority**: Without session creation, no other functionality can work. This is the entry point for the entire workflow.

**Independent Test**: Can be fully tested by running the CLI, selecting "start session", and verifying a valid UUID is displayed. Delivers the foundation for all collaboration.

**Acceptance Scenarios**:

1. **Given** the Coordination Service is running, **When** the Approver runs the CLI and selects "start session", **Then** the system displays a newly generated Session ID (UUID format)
2. **Given** a session has been created, **When** the Session ID is displayed, **Then** the Approver can copy/share this ID with a Requester
3. **Given** a session is started, **When** the CLI enters the approval loop, **Then** it displays a waiting state indicating it's ready to receive requests

---

### User Story 2 - Requester Joins Session and Views History (Priority: P1)

As a Requester, I want to join an existing session using a Session ID so that I can submit approval requests and see the session history.

**Why this priority**: This enables the second actor to participate, completing the two-party communication requirement. Equal priority with US1 as both are needed for basic functionality.

**Independent Test**: Can be tested by entering a valid Session ID in the web UI and verifying the session history panel loads (even if empty for a new session).

**Acceptance Scenarios**:

1. **Given** the web application is loaded, **When** the user enters a valid Session ID and submits, **Then** the application connects to the session and displays the session view
2. **Given** a session has previous requests and decisions, **When** the Requester joins, **Then** all historical requests with their outcomes (Approved/Rejected) are displayed in chronological order
3. **Given** a new session with no history, **When** the Requester joins, **Then** an empty history is shown with an enabled input field for new requests
4. **Given** an invalid Session ID is entered, **When** the user attempts to join, **Then** an error message is displayed indicating the session does not exist

---

### User Story 3 - Requester Submits Request (Priority: P2)

As a Requester, I want to submit a text request for approval so that the Approver can review and decide on it.

**Why this priority**: Enables the core submission flow, but depends on session joining (US2) being functional first.

**Independent Test**: Can be tested by joining a session, typing text in the input field, and submitting. Verifies the request appears in the pending state.

**Acceptance Scenarios**:

1. **Given** a Requester is connected to a session with an enabled input field, **When** they type text and submit, **Then** the request is sent to the Coordination Service
2. **Given** a request is submitted, **When** the submission is acknowledged, **Then** the input field becomes disabled and a "waiting for approval" indicator is shown
3. **Given** a request is pending, **When** the Requester attempts to submit another request, **Then** the submission is blocked (input field remains disabled)
4. **Given** a request is submitted, **When** the Approver is connected, **Then** the request text appears on the Approver's CLI

---

### User Story 4 - Approver Reviews and Decides (Priority: P2)

As an Approver, I want to review incoming requests and make approve/reject decisions so that Requesters receive timely responses.

**Why this priority**: Completes the approval workflow cycle. Depends on request submission (US3) being functional.

**Independent Test**: Can be tested by having a pending request arrive, displaying it, and entering 'y' or 'n' to see the decision recorded.

**Acceptance Scenarios**:

1. **Given** the Approver CLI is in waiting state, **When** a new request arrives, **Then** the request text is displayed clearly to the Approver
2. **Given** a request is displayed, **When** the Approver enters 'y', **Then** an "Approved" decision is sent to the server
3. **Given** a request is displayed, **When** the Approver enters 'n', **Then** a "Rejected" decision is sent to the server
4. **Given** a decision is sent, **When** the server acknowledges it, **Then** the CLI returns to the waiting state for the next request

---

### User Story 5 - Requester Receives Real-Time Decision (Priority: P2)

As a Requester, I want to see the Approver's decision in real-time without refreshing so that I can proceed with my next action immediately.

**Why this priority**: Provides the real-time feedback loop that demonstrates gRPC streaming capabilities. Depends on US3 and US4.

**Independent Test**: Can be tested by submitting a request from web UI, making a decision in CLI, and verifying the web UI updates automatically with the decision.

**Acceptance Scenarios**:

1. **Given** a Requester has a pending request, **When** the Approver approves it, **Then** the Requester's UI automatically updates to show "Approved" without page refresh
2. **Given** a Requester has a pending request, **When** the Approver rejects it, **Then** the Requester's UI automatically updates to show "Rejected" without page refresh
3. **Given** a decision is received, **When** the UI updates, **Then** the decision is added to the session history log
4. **Given** a decision is received, **When** the UI updates, **Then** the input field is re-enabled for the next request

---

### User Story 6 - Approver Continues Existing Session (Priority: P3)

As an Approver, I want to reconnect to an existing session so that I can resume approving requests after disconnecting.

**Why this priority**: Provides session resilience but is not essential for demonstrating the core streaming concept.

**Independent Test**: Can be tested by starting a session, noting the ID, exiting the CLI, then reconnecting with "continue session" and the same ID.

**Acceptance Scenarios**:

1. **Given** the CLI is started, **When** the Approver selects "continue session" and enters a valid Session ID, **Then** the CLI connects to the existing session
2. **Given** reconnection is successful, **When** the CLI enters the approval loop, **Then** any pending requests in that session are displayed for review
3. **Given** an invalid Session ID is entered, **When** connection is attempted, **Then** an error message is displayed and the user can retry

---

### Edge Cases

- What happens when the Approver disconnects while a request is pending? (Assumption: Request remains pending until Approver reconnects)
- What happens when the Requester disconnects while waiting for a decision? (Assumption: Decision is stored; Requester sees it upon reconnection)
- What happens when the Coordination Service restarts? (Assumption: All sessions and history are lost; this is acceptable per in-memory requirement)
- What happens when the Web UI loses connection to the Coordination Service? (Clarified: Display connection-lost indicator and auto-reconnect with visual feedback)
- What happens when the Requester submits an empty request? (Assumption: Empty submissions are rejected with validation error)
- What happens when multiple Requesters join the same session? (Clarified: All Requesters see the same history; concurrent submissions are queued and processed FIFO by the Approver)

## Requirements *(mandatory)*

### Functional Requirements

**Coordination Service:**
- **FR-001**: Service MUST generate unique Session IDs using UUID format
- **FR-002**: Service MUST maintain session state entirely in-memory during runtime
- **FR-003**: Service MUST support real-time bidirectional message passing between connected clients
- **FR-004**: Service MUST relay requests from Requester to Approver without polling
- **FR-005**: Service MUST relay decisions from Approver to Requester without polling
- **FR-006**: Service MUST persist session history (requests and decisions) for the session's lifetime
- **FR-006a**: Service MUST queue concurrent requests from multiple Requesters and present them to the Approver sequentially (FIFO order)

**Approver CLI:**
- **FR-007**: CLI MUST provide option to start a new session
- **FR-008**: CLI MUST provide option to continue an existing session by entering a Session ID
- **FR-009**: CLI MUST display newly generated Session ID when starting a session
- **FR-010**: CLI MUST display incoming request text when a request arrives
- **FR-011**: CLI MUST accept 'y' for Approve and 'n' for Reject as decision inputs
- **FR-012**: CLI MUST enter a blocking wait state when no requests are pending

**Requester Web UI:**
- **FR-013**: Web UI MUST prompt for Session ID on initial load
- **FR-014**: Web UI MUST display session history upon successful connection
- **FR-015**: Web UI MUST provide a text input field for submitting requests
- **FR-016**: Web UI MUST disable the input field while a request is pending
- **FR-017**: Web UI MUST display a waiting indicator while a request is pending
- **FR-018**: Web UI MUST update automatically when a decision is received (no page refresh)
- **FR-019**: Web UI MUST re-enable the input field after a decision is received
- **FR-020**: Web UI MUST display a connection-lost indicator when disconnected from the Coordination Service
- **FR-021**: Web UI MUST attempt automatic reconnection with visual feedback showing reconnection status

### Non-Functional Requirements

**Observability:**
- **NFR-001**: Coordination Service MUST output info-level logs to stdout (visible in server terminal)
- **NFR-002**: Info-level logs MUST include: client connections/disconnections, requests received, decisions made
- **NFR-003**: Coordination Service MUST write verbose-level logs (including internal state transitions and message details) to a log file
- **NFR-004**: Log file location SHOULD be configurable, defaulting to `./logs/coordination-service.log`

### Key Entities

- **Session**: An ephemeral workspace for approval communication; identified by a unique UUID; contains a collection of Requests; exists only in-memory during service runtime
- **Request**: A text submission from a Requester requiring a decision; belongs to exactly one Session; transitions through states: `Pending` → `Approved` | `Rejected` (two terminal states); contains the request text and decision outcome
- **Decision**: A binary outcome (Approved/Rejected) for a Request; made by the Approver; permanently associated with its Request within the session lifetime

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Requester can submit a request and receive a decision within 5 seconds of the Approver making the decision (demonstrates real-time communication)
- **SC-002**: Session history displays all requests and decisions in correct chronological order with 100% accuracy
- **SC-003**: Users can complete the full workflow (start session → join session → submit request → receive decision) in under 2 minutes on first attempt
- **SC-004**: Approver can process at least 10 consecutive requests in a single session without disconnection or errors
- **SC-005**: Web UI updates automatically upon decision without any user-initiated refresh action
- **SC-006**: CLI provides clear feedback at each state transition (waiting, request received, decision sent)

## Out of Scope

The following are explicitly excluded from this prototype:

- **Authentication/Authorization**: No user login, identity verification, or role-based access control. Users are identified solely by their role (Approver/Requester) within a session.
- **Data Persistence**: No database or durable storage. All session data exists only in-memory and is lost when the Coordination Service stops.
- **Production Deployment**: No containerization, load balancing, TLS/SSL, or production-grade infrastructure. Development servers only.

## Clarifications

### Session 2025-12-28

- Q: What functionality should be explicitly excluded from this prototype? → A: Authentication, persistence (database), and production deployment concerns
- Q: What states should a Request transition through? → A: Pending → Approved/Rejected (two terminal states)
- Q: What level of logging should the Coordination Service provide? → A: Info-level to stdout (terminal), verbose-level to log file
- Q: How should concurrent request submissions from multiple Requesters be handled? → A: Queue requests; Approver processes them sequentially (FIFO)
- Q: How should the Web UI behave when it loses connection to the Coordination Service? → A: Display connection-lost indicator; auto-reconnect with visual feedback

## Assumptions

- The Coordination Service, Approver CLI, and Requester Web UI will run on the same local network or machine during development/testing
- Session IDs are shared out-of-band (e.g., copy/paste, verbal communication) between Approver and Requester
- A single Approver is active per session at any time
- Request text has no maximum length restriction for this prototype
- The web application will be served by a simple development server (not production-grade)
- gRPC will be used for real-time bidirectional streaming between components
