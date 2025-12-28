# Tasks: Real-Time Approval Workflow

**Input**: [plan.md](plan.md), [spec.md](spec.md)  
**Feature Branch**: `001-approval-workflow`  
**Created**: 2025-12-28

## Format: `[ID] [P?] [PR#] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[PR#]**: Which pull request this task belongs to
- Include exact file paths in descriptions

---

## Phase 1: PR #1 - Environment Updates

**Goal**: Configure dev container with all dependencies using Backup-Restore pattern and Split CI workflows.

**Strategy**: 
- **Backup-Restore Pattern**: Install deps in Dockerfile → backup node_modules → restore via init.sh
- **Split CI Workflows**: Builder (on dep changes) + Runner (on all changes, never pushes)

### Git Setup for PR #1

- [x] T001 Sync main branch: `git checkout main && git pull origin main`
- [x] T002 Create feature branch: `git checkout -b pr1-environment-updates`

### Dockerfile Updates [PR1]

- [x] T003 [PR1] Rewrite .devcontainer/Dockerfile with Backup-Restore pattern:
  - Add `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv`
  - Set `ENV UV_LINK_MODE=copy` and `ENV UV_CACHE_DIR=/opt/uv-cache`
  - Install Node.js and npm via apt-get
  - Install Angular CLI globally (`npm install -g @angular/cli`)
  - Copy lockfiles first (pyproject.toml, uv.lock, package.json, package-lock.json)
  - Run `uv sync --frozen --no-install-project`
  - Run `npm install && cp -r node_modules /opt/backup/node_modules`
  - Add final `COPY . .` for CI

### Initialization Script [PR1]

- [x] T004 [PR1] Create .devcontainer/init.sh with restore logic:
  - Check if node_modules exists/empty → restore from /opt/backup
  - Run `npm install` to catch drift
  - Run `uv sync` to sync Python environment
  - Make executable: `chmod +x .devcontainer/init.sh`

### DevContainer Configuration [PR1]

- [x] T005 [P] [PR1] Update .devcontainer/devcontainer.json:
  - Add docker-in-docker feature: `"ghcr.io/devcontainers/features/docker-in-docker:2": {"enableNonRootDocker": "true"}`
  - Remove Node.js devcontainer feature (installed in Dockerfile)
  - Set `"postCreateCommand": "bash .devcontainer/init.sh"`
  - Add uv-cache volume mount: `"source=uv-cache,target=/opt/uv-cache,type=volume"`
  - Configure port forwarding (4200, 8080, 50051)
  - Add VS Code extensions (angular.ng-template, zxh404.vscode-proto3)

### Python Dependencies [PR1]

- [x] T006 [P] [PR1] Add betterproto[compiler] and grpclib to pyproject.toml dev dependencies
- [x] T007 [PR1] Run `uv lock` to update uv.lock with new dependencies

### Node Dependencies [PR1]

- [x] T008 [PR1] Create root package.json with Angular CLI as devDependency
- [x] T009 [PR1] Run `npm install` to generate package-lock.json

### CI Workflows [PR1]

- [x] T010 [P] [PR1] Create .github/workflows/build-image.yaml (The Builder):
  - Trigger on push to main with paths: .devcontainer/**, pyproject.toml, uv.lock, package.json, package-lock.json
  - Login to GHCR
  - Use devcontainers/ci@v0.3 with `push: always`

- [x] T011 [P] [PR1] Update .github/workflows/ci.yaml (The Runner):
  - Trigger on push/PR to main (all paths)
  - Login to GHCR
  - Use devcontainers/ci@v0.3 with `push: never`
  - cacheFrom: ghcr.io/${{ github.repository }}/devcontainer

### Cleanup [PR1]

- [x] T012 [PR1] Remove .devcontainer/setup-env.sh (replaced by init.sh)
- [x] T013 [PR1] Remove .devcontainer/post-start.sh (if exists and not needed)
- [x] T014 [PR1] Remove obsolete mounts (gh_token_file if not needed)

### Verification for PR #1

- [ ] T015 [PR1] Verify devcontainer builds successfully: rebuild container
- [x] T016 [PR1] Run `./scripts/check_quality.sh` - must pass
- [ ] T017 [PR1] Verify `docker compose version` works (DinD enabled)
- [ ] T018 [PR1] Verify `node --version` shows Node.js installed
- [ ] T019 [PR1] Verify `ng version` shows Angular CLI installed
- [ ] T020 [PR1] Verify `python -c "import betterproto"` succeeds
- [ ] T021 [PR1] Verify `python -c "import grpclib"` succeeds
- [ ] T022 [PR1] Verify node_modules restored after rebuild (check init.sh ran)
- [ ] T023 [PR1] Verify uv-cache volume exists: `docker volume ls | grep uv-cache`

### Git Workflow for PR #1

- [ ] T024 Push branch and create PR: `git push -u origin pr1-environment-updates && gh pr create --title "PR #1: Environment Updates" --body "Implements Backup-Restore pattern for deps, Split CI workflows (Builder + Runner)"`
- [ ] T025 Monitor CI checks: `gh pr checks --watch`
- [ ] T026 Address any CI failures until checks pass
- [ ] T027 **STOP**: Ask user to review PR #1
- [ ] T028 Squash merge after approval: `gh pr merge --squash --delete-branch`

### Post-PR #1 Actions

- [ ] T029 **USER ACTION**: Rebuild dev container before continuing
- [ ] T030 Verify build-image.yaml triggered and pushed image to GHCR

**Checkpoint**: Dev container uses Backup-Restore pattern. CI uses Split Workflow (Builder + Runner). User must rebuild before Phase 2.

---

## Phase 2: PR #2 - Directory Layout & Boilerplate

**Goal**: Establish project structure with minimal scaffolding. No business logic—just skeleton.

### Git Setup for PR #2

- [ ] T031 Sync main branch: `git checkout main && git pull origin main`
- [ ] T032 Create feature branch: `git checkout -b pr2-boilerplate`

### Proto Files [PR2]

- [ ] T033 [P] [PR2] Create protos/approval_request.proto with RequestStatus enum and ApprovalRequest message
- [ ] T034 [P] [PR2] Create protos/session.proto with Session and SessionEvent messages
- [ ] T035 [P] [PR2] Create protos/approval_service.proto with ApprovalService definition

### Proto Generation [PR2]

- [ ] T036 [PR2] Create scripts/gen_protos.sh for betterproto code generation
- [ ] T037 [PR2] Run gen_protos.sh and verify rpc_stream_prototype/generated/ is created
- [ ] T038 [PR2] Add __init__.py files to generated/approval/ directories

### Python Package Restructure [PR2]

- [ ] T039 [PR2] Create rpc_stream_prototype/backend/__init__.py
- [ ] T040 [PR2] Create rpc_stream_prototype/backend/main.py with stub serve() function
- [ ] T041 [PR2] Create rpc_stream_prototype/backend/services/__init__.py
- [ ] T042 [PR2] Create rpc_stream_prototype/cli/main.py with stub typer commands (start, join)
- [ ] T043 [PR2] Create rpc_stream_prototype/cli/ui/__init__.py
- [ ] T044 [PR2] Create rpc_stream_prototype/shared/__init__.py
- [ ] T045 [PR2] Move logging_config.py to rpc_stream_prototype/shared/logging_config.py
- [ ] T046 [PR2] Update pyproject.toml with new entry points (rpc-server, rpc-cli)
- [ ] T047 [PR2] Remove old rpc_stream_prototype/cli/app.py and update imports

### Angular Scaffold [PR2]

- [ ] T048 [PR2] Run `ng new frontend --routing --style=scss --skip-git --package-manager=npm` in frontend/ directory
- [ ] T049 [PR2] Install Angular dependencies: `cd frontend && npm install @angular/material @angular/cdk`
- [ ] T050 [PR2] Install Connect-ES dependencies: `npm install @connectrpc/connect @connectrpc/connect-web @bufbuild/protobuf`
- [ ] T051 [PR2] Configure angular.json with poll option for Docker/WSL compatibility

### Docker Configuration [PR2]

- [ ] T052 [PR2] Create docker/backend.Dockerfile with Python 3.14, uv, watchfiles
- [ ] T053 [PR2] Create docker/frontend.Dockerfile with Node 22
- [ ] T054 [PR2] Create docker-compose.yaml with backend, frontend, envoy services
- [ ] T055 [PR2] Create envoy/envoy.yaml with gRPC-Web to gRPC proxy configuration

### Project Setup [PR2]

- [ ] T056 [PR2] Create logs/.gitkeep and logs/.gitignore (ignore *.log)
- [ ] T057 [PR2] Update .gitignore with generated/, node_modules/, logs/*.log
- [ ] T058 [PR2] Create tests/fixtures/__init__.py (shared test fixtures directory per Constitution)

### Verification for PR #2

- [ ] T059 [PR2] Verify `python -c "from rpc_stream_prototype.generated.approval.v1 import *"` succeeds
- [ ] T060 [PR2] Verify `docker compose build` completes successfully
- [ ] T061 [PR2] Verify `docker compose up` starts all three services
- [ ] T062 [PR2] Verify frontend accessible at http://localhost:4200
- [ ] T063 [PR2] Verify Envoy listening on port 8080
- [ ] T064 [PR2] Verify `./scripts/check_quality.sh` passes

### Git Workflow for PR #2

- [ ] T065 Push branch and create PR: `git push -u origin pr2-boilerplate && gh pr create --title "PR #2: Directory Layout & Boilerplate" --body "Project structure, Angular scaffold, Docker Compose, Envoy config, proto files"`
- [ ] T066 Monitor CI checks: `gh pr checks --watch`
- [ ] T067 Address any CI failures until checks pass
- [ ] T068 **STOP**: Ask user to review PR #2
- [ ] T069 Squash merge after approval: `gh pr merge --squash --delete-branch`

**Checkpoint**: Project skeleton complete. Docker Compose runs all services (stubs). Proto generation works.

---

## Phase 3: PR #3 - Server Implementation

**Goal**: Complete backend with all gRPC service methods, in-memory storage, logging, and tests.

### Git Setup for PR #3

- [ ] T070 Sync main branch: `git checkout main && git pull origin main`
- [ ] T071 Create feature branch: `git checkout -b pr3-server-implementation`

### Domain Models [PR3]

- [ ] T072 [PR3] Create rpc_stream_prototype/backend/models/__init__.py
- [ ] T073 [PR3] Create rpc_stream_prototype/backend/models/domain.py with RequestStatus enum, ApprovalRequest, Session dataclasses

### Storage Layer [PR3]

- [ ] T074 [PR3] Create rpc_stream_prototype/backend/storage/__init__.py
- [ ] T075 [PR3] Create rpc_stream_prototype/backend/storage/repository.py with SessionRepository ABC
- [ ] T076 [PR3] Create rpc_stream_prototype/backend/storage/memory_store.py with InMemorySessionRepository implementation

### Event Broadcasting [PR3]

- [ ] T077 [PR3] Create rpc_stream_prototype/backend/events/__init__.py
- [ ] T078 [PR3] Create rpc_stream_prototype/backend/events/broadcaster.py with EventBroadcaster class (subscribe, unsubscribe, broadcast)

### Logging [PR3]

- [ ] T079 [PR3] Create rpc_stream_prototype/backend/logging.py with dual logging (INFO→stdout, VERBOSE→file)

### gRPC Service [PR3]

- [ ] T080 [PR3] Create rpc_stream_prototype/backend/services/approval_service.py with ApprovalServiceImpl
- [ ] T081 [PR3] Implement CreateSession RPC (FR-001, FR-002)
- [ ] T082 [PR3] Implement GetSession RPC (FR-002)
- [ ] T083 [PR3] Implement Subscribe RPC with history replay + live streaming (FR-003, FR-004, FR-005, FR-006)
- [ ] T084 [PR3] Implement SubmitRequest RPC with FIFO queuing (FR-004, FR-006a)
- [ ] T085 [PR3] Implement SubmitDecision RPC (FR-005)

### Server Entry Point [PR3]

- [ ] T086 [PR3] Update rpc_stream_prototype/backend/main.py with full server initialization

### Shared Test Fixtures [PR3]

- [ ] T087 [P] [PR3] Create tests/fixtures/fake_repository.py with FakeSessionRepository (in-memory, state-verifiable per Constitution)
- [ ] T088 [P] [PR3] Create tests/fixtures/fake_broadcaster.py with FakeBroadcaster (event recording for state verification)

### Unit Tests [PR3]

- [ ] T089 [P] [PR3] Create tests/unit/backend/__init__.py
- [ ] T090 [P] [PR3] Create tests/unit/backend/test_domain.py (model creation, state transitions)
- [ ] T091 [P] [PR3] Create tests/unit/backend/test_memory_store.py (repository operations, concurrency)
- [ ] T092 [P] [PR3] Create tests/unit/backend/test_broadcaster.py (subscribe/unsubscribe, event delivery)
- [ ] T093 [P] [PR3] Create tests/unit/backend/test_approval_service.py using FakeSessionRepository and FakeBroadcaster

### Integration Tests [PR3]

- [ ] T094 [PR3] Create tests/integration/test_server_e2e.py (full server startup, gRPC calls, streaming)

### Verification for PR #3

- [ ] T095 [PR3] Run `pytest tests/unit/backend/` - all tests pass
- [ ] T096 [PR3] Run `pytest tests/integration/` - all tests pass
- [ ] T097 [PR3] Verify server starts with `docker compose up backend`
- [ ] T098 [PR3] Verify INFO logs appear in stdout
- [ ] T099 [PR3] Verify verbose logs appear in logs/coordination-service.log
- [ ] T100 [PR3] Verify `./scripts/check_quality.sh` passes

### Git Workflow for PR #3

- [ ] T101 Push branch and create PR: `git push -u origin pr3-server-implementation && gh pr create --title "PR #3: Server Implementation" --body "Full backend with gRPC service, in-memory storage, event broadcasting, logging, and tests"`
- [ ] T102 Monitor CI checks: `gh pr checks --watch`
- [ ] T103 Address any CI failures until checks pass
- [ ] T104 **STOP**: Ask user to review PR #3
- [ ] T105 Squash merge after approval: `gh pr merge --squash --delete-branch`

**Checkpoint**: Server fully functional. All RPC methods implemented and tested. Logging works.

---

## Phase 4: PR #4 - Approver CLI Implementation

**Goal**: Complete CLI for Approvers to start/join sessions and process approval requests.

### Git Setup for PR #4

- [ ] T106 Sync main branch: `git checkout main && git pull origin main`
- [ ] T107 Create feature branch: `git checkout -b pr4-cli-implementation`

### gRPC Client [PR4]

- [ ] T108 [PR4] Create rpc_stream_prototype/cli/client/__init__.py
- [ ] T109 [PR4] Create rpc_stream_prototype/cli/client/grpc_client.py with ApprovalClient wrapper

### UI Components [PR4]

- [ ] T110 [P] [PR4] Create rpc_stream_prototype/cli/ui/console.py with Rich console setup
- [ ] T111 [P] [PR4] Create rpc_stream_prototype/cli/ui/display.py (display_session_id, display_waiting_state, display_request, display_decision_sent)
- [ ] T112 [P] [PR4] Create rpc_stream_prototype/cli/ui/prompts.py (prompt_session_action, prompt_session_id, prompt_decision)

### Session Management [PR4]

- [ ] T113 [PR4] Create rpc_stream_prototype/cli/session/__init__.py
- [ ] T114 [PR4] Create rpc_stream_prototype/cli/session/approval_loop.py with run_approval_loop function

### CLI Entry Point [PR4]

- [ ] T115 [PR4] Update rpc_stream_prototype/cli/main.py with full implementation (FR-007, FR-008, FR-009, FR-010, FR-011, FR-012)

### Shared Test Fixtures [PR4]

- [ ] T116 [PR4] Create tests/fixtures/fake_approval_client.py with FakeApprovalClient (canned responses, state-verifiable per Constitution)

### Unit Tests [PR4]

- [ ] T117 [P] [PR4] Create tests/unit/cli/__init__.py
- [ ] T118 [P] [PR4] Create tests/unit/cli/test_grpc_client.py using FakeApprovalClient (no network calls)
- [ ] T119 [P] [PR4] Create tests/unit/cli/test_prompts.py (input validation, choice handling)
- [ ] T120 [P] [PR4] Create tests/unit/cli/test_approval_loop.py using FakeApprovalClient (event processing, decision flow)

### Integration Tests [PR4]

- [ ] T121 [PR4] Create tests/integration/test_cli_e2e.py (full CLI flow with real server)

### Verification for PR #4

- [ ] T122 [PR4] Run `pytest tests/unit/cli/` - all tests pass
- [ ] T123 [PR4] Run `pytest tests/integration/test_cli_e2e.py` - all tests pass
- [ ] T124 [PR4] Verify CLI starts with `rpc-cli` or `python -m rpc_stream_prototype.cli.main`
- [ ] T125 [PR4] Verify can create session and see UUID displayed
- [ ] T126 [PR4] Verify can continue existing session
- [ ] T127 [PR4] Verify requests display when received and decisions are sent
- [ ] T128 [PR4] Verify `./scripts/check_quality.sh` passes

### Git Workflow for PR #4

- [ ] T129 Push branch and create PR: `git push -u origin pr4-cli-implementation && gh pr create --title "PR #4: Approver CLI Implementation" --body "Full CLI with gRPC client, Rich UI components, approval loop, and tests"`
- [ ] T130 Monitor CI checks: `gh pr checks --watch`
- [ ] T131 Address any CI failures until checks pass
- [ ] T132 **STOP**: Ask user to review PR #4
- [ ] T133 Squash merge after approval: `gh pr merge --squash --delete-branch`

**Checkpoint**: CLI fully functional. Approver can start/continue sessions and process requests.

---

## Phase 5: PR #5 - Angular App Implementation

**Goal**: Complete web application for Requesters to join sessions, submit requests, and receive real-time decisions.

### Git Setup for PR #5

- [ ] T134 Sync main branch: `git checkout main && git pull origin main`
- [ ] T135 Create feature branch: `git checkout -b pr5-angular-app`

### TypeScript Proto Generation [PR5]

- [ ] T136 [PR5] Create frontend/buf.gen.yaml with Connect-ES plugins
- [ ] T137 [PR5] Add "generate" script to frontend/package.json
- [ ] T138 [PR5] Run buf generate and verify frontend/src/generated/ is created

### Core Services [PR5]

- [ ] T139 [PR5] Create frontend/src/app/core/services/approval.service.ts with Connect-ES gRPC client
- [ ] T140 [PR5] Create frontend/src/app/core/services/session-state.service.ts with Angular Signals state management
- [ ] T141 [PR5] Create frontend/src/app/core/models/types.ts with TypeScript interfaces

### Join Session Feature [PR5]

- [ ] T142 [PR5] Create frontend/src/app/features/join-session/join-session.component.ts (FR-013)
- [ ] T143 [PR5] Create frontend/src/app/features/join-session/join-session.component.html with Material form
- [ ] T144 [PR5] Create frontend/src/app/features/join-session/join-session.component.scss

### Session Feature - Main Component [PR5]

- [ ] T145 [PR5] Create frontend/src/app/features/session/session.component.ts with subscription and auto-reconnect
- [ ] T146 [PR5] Create frontend/src/app/features/session/session.component.html
- [ ] T147 [PR5] Create frontend/src/app/features/session/session.component.scss

### Session Feature - Child Components [PR5]

- [ ] T148 [P] [PR5] Create frontend/src/app/features/session/components/history-panel/history-panel.component.ts (FR-014)
- [ ] T149 [P] [PR5] Create frontend/src/app/features/session/components/request-form/request-form.component.ts (FR-015, FR-016, FR-017, FR-019)
- [ ] T150 [P] [PR5] Create frontend/src/app/features/session/components/connection-status/connection-status.component.ts (FR-020, FR-021)

### Shared Components [PR5]

- [ ] T151 [PR5] Create frontend/src/app/shared/components/loading-spinner/loading-spinner.component.ts

### Routing & Configuration [PR5]

- [ ] T152 [PR5] Update frontend/src/app/app.routes.ts with routes ('', 'session/:id')
- [ ] T153 [PR5] Update frontend/src/app/app.component.ts with router-outlet
- [ ] T154 [PR5] Configure Angular Material theme in frontend/src/styles.scss

### Unit Tests [PR5]

- [ ] T155 [P] [PR5] Create frontend/src/app/core/services/approval.service.spec.ts
- [ ] T156 [P] [PR5] Create frontend/src/app/core/services/session-state.service.spec.ts
- [ ] T157 [P] [PR5] Create frontend/src/app/features/join-session/join-session.component.spec.ts
- [ ] T158 [P] [PR5] Create frontend/src/app/features/session/session.component.spec.ts
- [ ] T159 [P] [PR5] Create frontend/src/app/features/session/components/history-panel/history-panel.component.spec.ts
- [ ] T160 [P] [PR5] Create frontend/src/app/features/session/components/request-form/request-form.component.spec.ts
- [ ] T161 [P] [PR5] Create frontend/src/app/features/session/components/connection-status/connection-status.component.spec.ts

### E2E Tests [PR5]

- [ ] T162 [PR5] Create frontend/e2e/join-session.spec.ts (join flow, validation errors)
- [ ] T163 [PR5] Create frontend/e2e/session-workflow.spec.ts (full request/decision flow)
- [ ] T164 [PR5] Create frontend/e2e/reconnection.spec.ts (connection loss handling)

### Verification for PR #5

- [ ] T165 [PR5] Run `cd frontend && ng test` - all unit tests pass
- [ ] T166 [PR5] Run `cd frontend && ng e2e` - all E2E tests pass
- [ ] T167 [PR5] Run `cd frontend && ng build` - build succeeds
- [ ] T168 [PR5] Verify can join session via UI
- [ ] T169 [PR5] Verify can submit request and input disables
- [ ] T170 [PR5] Verify real-time updates work (< 5 seconds latency per SC-001)
- [ ] T171 [PR5] Verify history displays correctly (SC-002)
- [ ] T172 [PR5] Verify connection status shows correctly and auto-reconnect works
- [ ] T173 [PR5] Verify `./scripts/check_quality.sh` passes

### Git Workflow for PR #5

- [ ] T174 Push branch and create PR: `git push -u origin pr5-angular-app && gh pr create --title "PR #5: Angular App Implementation" --body "Full Requester web UI with session joining, request submission, real-time updates, auto-reconnect, and tests"`
- [ ] T175 Monitor CI checks: `gh pr checks --watch`
- [ ] T176 Address any CI failures until checks pass
- [ ] T177 **STOP**: Ask user to review PR #5
- [ ] T178 Squash merge after approval: `gh pr merge --squash --delete-branch`

**Checkpoint**: Angular app fully functional. Full approval workflow works end-to-end.

---

## Phase 6: Final Validation

**Goal**: End-to-end workflow validation against success criteria.

- [ ] T179 Sync main branch: `git checkout main && git pull origin main`
- [ ] T180 Run full system: `docker compose up`
- [ ] T181 Validate SC-001: Request → Decision latency < 5 seconds
- [ ] T182 Validate SC-002: History displays correctly in chronological order
- [ ] T183 Validate SC-003: Full workflow completable in < 2 minutes
- [ ] T184 Validate SC-004: Process 10 consecutive requests without errors
- [ ] T185 Validate SC-005: Web UI updates without manual refresh
- [ ] T186 Validate SC-006: CLI provides clear feedback at each state

**Checkpoint**: All success criteria validated. Feature complete.

---

## Dependencies & Execution Order

### PR Dependencies

```
PR #1 (Environment)
    │
    ▼ [USER: rebuild devcontainer]
PR #2 (Boilerplate)
    │
    ▼
PR #3 (Server)
    │
    ├─────────────────┐
    ▼                 ▼
PR #4 (CLI)      PR #5 (Angular)
    │                 │
    └────────┬────────┘
             ▼
    Final Validation
```

### Parallel Opportunities

**Within PR #1**: T003-T011 can run in parallel (different files: Dockerfile, devcontainer.json, pyproject.toml, package.json, workflows)

**Within PR #2**: T033-T035 (proto files), T039-T047 (Python restructure) can run in parallel

**Within PR #3**: T087-T088 (shared fixtures), T089-T093 (unit tests) can run in parallel after service implementation

**Within PR #4**: T110-T112 (UI components), T117-T120 (unit tests) can run in parallel

**Within PR #5**: T148-T150 (child components), T155-T161 (unit tests) can run in parallel

**Cross-PR**: After PR #3 merges, PR #4 and PR #5 can be worked on in parallel by different developers

---

## Summary

| PR | Tasks | Parallelizable | Blocking |
|----|-------|----------------|----------|
| #1 | T001-T030 | 9 | Devcontainer rebuild, CI image push |
| #2 | T031-T069 | 8 | Proto generation |
| #3 | T070-T105 | 7 | Server must work |
| #4 | T106-T133 | 7 | Requires PR #3 |
| #5 | T134-T178 | 10 | Requires PR #3 |
| Final | T179-T186 | 0 | Requires all PRs |

**Total Tasks**: 186  
**Total PRs**: 5  
**Suggested MVP**: PR #1 + PR #2 + PR #3 + PR #4 (CLI can demonstrate core workflow)

---

## Notes

- [P] tasks can run in parallel (different files, no dependencies)
- [PR#] maps task to specific pull request
- Each PR must pass CI before merge
- User review required before each merge
- Rebuild devcontainer after PR #1 merge
- PR #4 and PR #5 can proceed in parallel after PR #3
- Shared test fixtures in tests/fixtures/ per Constitution (Classicist approach)
- **CI Strategy**: Split Workflow (build-image.yaml + ci.yaml) for fast CI boot times
- **Dev Container Strategy**: Backup-Restore pattern for node_modules + uv-cache volume
