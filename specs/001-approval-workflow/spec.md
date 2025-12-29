# Feature Specification: Real-Time Approval Workflow

**Feature Branch**: `001-approval-workflow`  
**Created**: 2025-12-28  
**Status**: Draft  
**Input**: User description: Real-time Approval Workflow prototype with Coordination Service, Proposer CLI, and Approver Web UI

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Proposer Starts Session (Priority: P1)

As a Proposer, I want to start a new approval session from the CLI so that I can generate a Session ID to share with Approvers.

**Why this priority**: Without session creation, no other functionality can work. This is the entry point for the entire workflow.

**Independent Test**: Can be fully tested by running the CLI, selecting "start session", and verifying a valid UUID is displayed. Delivers the foundation for all collaboration.

**Acceptance Scenarios**:

1. **Given** the Coordination Service is running, **When** the Proposer runs the CLI and selects "start session", **Then** the system displays a newly generated Session ID (UUID format)
2. **Given** a session has been created, **When** the Session ID is displayed, **Then** the Proposer can copy/share this ID with an Approver
3. **Given** a session is started, **When** the CLI enters the proposal loop, **Then** it displays a prompt for entering a proposal description

---

### User Story 2 - Approver Joins Session and Views History (Priority: P1)

As an Approver, I want to join an existing session using a Session ID so that I can review proposals and see the session history.

**Why this priority**: This enables the second actor to participate, completing the two-party communication requirement. Equal priority with US1 as both are needed for basic functionality.

**Independent Test**: Can be tested by entering a valid Session ID in the web UI and verifying the session history panel loads (even if empty for a new session).

**Acceptance Scenarios**:

1. **Given** the web application is loaded, **When** the user enters a valid Session ID and submits, **Then** the application connects to the session and displays the session view
2. **Given** a session has previous proposals and decisions, **When** the Approver joins, **Then** all historical proposals with their outcomes (Approved/Rejected) are displayed in chronological order
3. **Given** a new session with no history, **When** the Approver joins, **Then** an empty history is shown with a waiting state for incoming proposals
4. **Given** an invalid Session ID is entered, **When** the user attempts to join, **Then** an error message is displayed indicating the session does not exist

---

### User Story 3 - Proposer Submits Proposal (Priority: P2)

As a Proposer, I want to submit a natural language proposal description for approval so that the Approver can review and decide on it.

**Why this priority**: Enables the core submission flow, but depends on session creation (US1) being functional first.

**Independent Test**: Can be tested by starting a session, typing text in the CLI prompt, and submitting. Verifies the proposal is sent to the server.

**Acceptance Scenarios**:

1. **Given** a Proposer has started a session with an active CLI prompt, **When** they type text and submit, **Then** the proposal is sent to the Coordination Service
2. **Given** a proposal is submitted, **When** the submission is acknowledged, **Then** a "waiting for decision" indicator is shown in the CLI
3. **Given** a proposal is pending, **When** the Proposer attempts to submit another proposal, **Then** the submission is blocked until the current proposal is decided
4. **Given** a proposal is submitted, **When** the Approver is connected, **Then** the proposal text appears on the Approver's Web UI

---

### User Story 4 - Approver Reviews and Decides (Priority: P2)

As an Approver, I want to review incoming proposals and make approve/reject decisions so that Proposers receive timely responses.

**Why this priority**: Completes the approval workflow cycle. Depends on proposal submission (US3) being functional.

**Independent Test**: Can be tested by having a pending proposal arrive in the web UI, displaying it, and clicking approve or reject to see the decision recorded.

**Acceptance Scenarios**:

1. **Given** the Approver Web UI is connected to a session, **When** a new proposal arrives, **Then** the proposal text is displayed clearly to the Approver
2. **Given** a proposal is displayed, **When** the Approver clicks "Approve", **Then** an "Approved" decision is sent to the server
3. **Given** a proposal is displayed, **When** the Approver clicks "Reject", **Then** a "Rejected" decision is sent to the server
4. **Given** a decision is sent, **When** the server acknowledges it, **Then** the UI returns to the waiting state for the next proposal

---

### User Story 5 - Proposer Receives Real-Time Decision (Priority: P2)

As a Proposer, I want to see the Approver's decision in real-time without polling so that I can proceed with my next action immediately.

**Why this priority**: Provides the real-time feedback loop that demonstrates gRPC streaming capabilities. Depends on US3 and US4.

**Independent Test**: Can be tested by submitting a proposal from CLI, making a decision in web UI, and verifying the CLI updates automatically with the decision.

**Acceptance Scenarios**:

1. **Given** a Proposer has a pending proposal, **When** the Approver approves it, **Then** the Proposer's CLI automatically updates to show "Approved" without polling
2. **Given** a Proposer has a pending proposal, **When** the Approver rejects it, **Then** the Proposer's CLI automatically updates to show "Rejected" without polling
3. **Given** a decision is received, **When** the CLI updates, **Then** the decision is added to the session history log
4. **Given** a decision is received, **When** the CLI updates, **Then** the prompt is re-enabled for the next proposal

---

### User Story 6 - Proposer Continues Existing Session (Priority: P3)

As a Proposer, I want to reconnect to an existing session so that I can resume submitting proposals after disconnecting.

**Why this priority**: Provides session resilience but is not essential for demonstrating the core streaming concept.

**Independent Test**: Can be tested by starting a session, noting the ID, exiting the CLI, then reconnecting with "continue session" and the same ID.

**Acceptance Scenarios**:

1. **Given** the CLI is started, **When** the Proposer selects "continue session" and enters a valid Session ID, **Then** the CLI connects to the existing session
2. **Given** reconnection is successful, **When** the CLI enters the proposal loop, **Then** any pending proposals in that session are displayed for review
3. **Given** an invalid Session ID is entered, **When** connection is attempted, **Then** an error message is displayed and the user can retry

---

### Edge Cases

- What happens when the Approver disconnects while a proposal is pending? (Assumption: Proposal remains pending until Approver reconnects)
- What happens when the Proposer disconnects while waiting for a decision? (Assumption: Decision is stored; Proposer sees it upon reconnection)
- What happens when the Coordination Service restarts? (Assumption: All sessions and history are lost; this is acceptable per in-memory requirement)
- What happens when the Web UI loses connection to the Coordination Service? (Clarified: Display connection-lost indicator and auto-reconnect with visual feedback)
- What happens when the Proposer submits an empty proposal? (Assumption: Empty submissions are rejected with validation error)
- What happens when multiple Approvers join the same session? (Clarified: All Approvers see the same history and incoming proposals; first to decide wins)

## Requirements *(mandatory)*

### Functional Requirements

**Coordination Service (Backend):**
- **FR-001**: Service MUST generate unique Session IDs using UUID format
- **FR-002**: Service MUST maintain session state entirely in-memory during runtime
- **FR-003**: Service MUST support real-time server-to-client streaming for pushing updates, combined with unary client-to-server RPCs for actions (Watch pattern)
- **FR-004**: Service MUST relay proposals from Proposer to Approver without polling
- **FR-005**: Service MUST relay decisions from Approver to Proposer without polling
- **FR-006**: Service MUST persist session history (proposals and decisions) for the session's lifetime
- **FR-006a**: Service MUST queue concurrent proposals and present them to Approvers sequentially (FIFO order)

**Proposer CLI:**
- **FR-007**: CLI MUST provide option to start a new session
- **FR-008**: CLI MUST provide option to continue an existing session by entering a Session ID
- **FR-009**: CLI MUST display newly generated Session ID when starting a session
- **FR-010**: CLI MUST provide a text prompt for entering proposal descriptions
- **FR-011**: CLI MUST display decision outcomes (Approved/Rejected) when received
- **FR-012**: CLI MUST enter a blocking wait state while a proposal is pending decision

**Approver Web UI:**
- **FR-013**: Web UI MUST prompt for Session ID on initial load
- **FR-014**: Web UI MUST display session history upon successful connection
- **FR-015**: Web UI MUST display incoming proposals clearly for review
- **FR-016**: Web UI MUST provide Approve and Reject buttons for decision input
- **FR-017**: Web UI MUST disable decision buttons while no proposal is pending
- **FR-018**: Web UI MUST update automatically when a new proposal arrives (no page refresh)
- **FR-019**: Web UI MUST display decision confirmation after submitting a decision
- **FR-020**: Web UI MUST display a connection-lost indicator when disconnected from the Coordination Service
- **FR-021**: Web UI MUST attempt automatic reconnection with visual feedback showing reconnection status

### Non-Functional Requirements

**Observability:**
- **NFR-001**: Coordination Service MUST output info-level logs to stdout (visible in server terminal)
- **NFR-002**: Info-level logs MUST include: client connections/disconnections, proposals received, decisions made
- **NFR-003**: Coordination Service MUST write verbose-level logs (including internal state transitions and message details) to a log file
- **NFR-004**: Log file location SHOULD be configurable, defaulting to `./logs/coordination-service.log`

### Key Entities

- **Session**: An ephemeral workspace for approval communication; identified by a unique UUID; contains a collection of Proposals; exists only in-memory during service runtime
- **Proposal**: A natural language description from a Proposer requiring a decision; belongs to exactly one Session; transitions through states: `Pending` → `Approved` | `Rejected` (two terminal states); contains the proposal text and decision outcome
- **Decision**: A binary outcome (Approved/Rejected) for a Proposal; made by the Approver; permanently associated with its Proposal within the session lifetime

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Proposer can submit a proposal and receive a decision within 5 seconds of the Approver making the decision (demonstrates real-time communication)
- **SC-002**: Session history displays all proposals and decisions in correct chronological order with 100% accuracy
- **SC-003**: Users can complete the full workflow (start session → join session → submit proposal → receive decision) in under 2 minutes on first attempt
- **SC-004**: Proposer can submit at least 10 consecutive proposals in a single session without disconnection or errors
- **SC-005**: CLI updates automatically upon decision without any user-initiated action
- **SC-006**: Web UI provides clear feedback at each state transition (waiting, proposal received, decision sent)

## Out of Scope

The following are explicitly excluded from this prototype:

- **Authentication/Authorization**: No user login, identity verification, or role-based access control. Users are identified solely by their role (Proposer/Approver) within a session.
- **Data Persistence**: No database or durable storage. All session data exists only in-memory and is lost when the Coordination Service stops.
- **Production Deployment**: No containerization, load balancing, TLS/SSL, or production-grade infrastructure. Development servers only.

## Clarifications

### Session 2025-12-28

- Q: What functionality should be explicitly excluded from this prototype? → A: Authentication, persistence (database), and production deployment concerns
- Q: What states should a Proposal transition through? → A: Pending → Approved/Rejected (two terminal states)
- Q: What level of logging should the Coordination Service provide? → A: Info-level to stdout (terminal), verbose-level to log file
- Q: How should concurrent proposal submissions be handled? → A: Queue proposals; Approver processes them sequentially (FIFO)
- Q: How should the Web UI behave when it loses connection to the Coordination Service? → A: Display connection-lost indicator; auto-reconnect with visual feedback

## Terminology

| Term | Context | Notes |
|------|---------|-------|
| Coordination Service | User-facing documentation | The backend server that coordinates approval workflows |
| Backend | Code artifacts, Docker | Python gRPC server implementation (`rpc_stream_prototype/backend/`) |
| Session ID | Documentation | User-visible identifier for a session |
| `session_id` | Python code | Snake_case variable/field name |
| `sessionId` | TypeScript code | CamelCase variable/field name |

## Assumptions

- The Coordination Service, Proposer CLI, and Approver Web UI will run on the same local network or machine during development/testing
- Session IDs are shared out-of-band (e.g., copy/paste, verbal communication) between Proposer and Approver
- A single active proposal is processed at a time per session
- Proposal text has no maximum length restriction for this prototype
- The web application will be served by a simple development server (not production-grade)
- gRPC will be used for real-time bidirectional streaming between components
