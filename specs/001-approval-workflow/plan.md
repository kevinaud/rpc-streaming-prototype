# Implementation Plan: Real-Time Approval Workflow

**Feature Branch**: `001-approval-workflow`  
**Spec**: [spec.md](spec.md)  
**Created**: 2025-12-28

---

## Architecture Overview

```
┌─────────────────┐     gRPC-Web (HTTP/1.1)     ┌─────────────┐     gRPC (HTTP/2)     ┌─────────────────┐
│  Angular Web UI │ ◄──────────────────────────► │ Envoy Proxy │ ◄───────────────────► │  Python Backend │
│   (Approver)    │        :8080                 │   :8080     │       :50051          │   (grpclib)     │
└─────────────────┘                              └─────────────┘                       └─────────────────┘
        ▲                                                                                      ▲
        │                                                                                      │
        │ Subscribe (Server-Side Stream)                                                       │
        │ SubmitDecision (Unary)                                                               │
        │                                                                                      │
        └──────────────────────────────────────────────────────────────────────────────────────┘
                                                                                               │
                                                                                   ┌───────────┴───────────┐
                                                                                   │    Python CLI         │
                                                                                   │    (Proposer)         │
                                                                                   │    betterproto client │
                                                                                   └───────────────────────┘
```

**Communication Pattern**: "Watch" pattern using Server-Side Streaming for real-time updates + Unary RPCs for actions.

---

## Pull Request Structure

| PR # | Title | Dependencies | Scope |
|------|-------|--------------|-------|
| 1 | Environment Updates | None | Dev container: docker-in-docker, Angular CLI, betterproto compiler |
| 2 | Directory Layout & Boilerplate | PR #1 merged + devcontainer rebuild | Project structure, Angular scaffold, Docker Compose, Envoy, proto stub |
| 3 | Server Implementation | PR #2 | Full backend with tests |
| 4 | Proposer CLI Implementation | PR #3 | Full CLI with tests |
| 5 | Angular App Implementation | PR #3 | Full web UI with tests |

---

## PR #1: Environment Updates

**Goal**: Configure the dev container with all dependencies needed for subsequent work. After merge and rebuild, no further devcontainer changes should be required.

### Strategy: Backup-Restore Pattern + Split CI Workflows

We solve the "Volume Overwrite" problem (source mount hides image-installed dependencies) using a **Backup-Restore Pattern**:

1. **Dockerfile**: Install dependencies and backup `node_modules` to `/opt/backup/`
2. **init.sh**: Restore backed-up dependencies after source mount, then sync to catch drift
3. **uv cache volume**: Persistent named volume for fast Python rebuilds

For CI, we use a **Split Workflow** strategy to minimize build times:

1. **build-image.yaml** (The Builder): Triggers only when dependency files change, pushes to GHCR
2. **ci.yaml** (The Runner): Triggers on all changes, pulls cached image, never pushes

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DOCKERFILE BUILD                                 │
│  1. Install Node.js & npm                                           │
│  2. Copy lockfiles (pyproject.toml, uv.lock, package*.json)         │
│  3. uv sync --frozen --no-install-project                           │
│  4. npm install && cp -r node_modules /opt/backup/                  │
│  5. COPY . . (for CI; ignored by dev container mount)               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DEV CONTAINER START                              │
│  1. Source code mounted (hides image's /app contents)               │
│  2. postCreateCommand runs init.sh:                                 │
│     - Restore node_modules from /opt/backup if missing              │
│     - npm install (catch drift)                                     │
│     - uv sync (catch drift + install local project)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Tasks

#### 1.1 Update Dockerfile with Backup-Restore Pattern
**File**: `.devcontainer/Dockerfile`

Complete rewrite to implement the backup-restore pattern:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.14

# 1. Setup uv (The fast Python installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/opt/uv-cache

# 2. Install Node.js & npm (for Angular development)
RUN apt-get update && apt-get install -y nodejs npm && \
    npm install -g @angular/cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Install Dependencies (The Cacheable Layer)
# Copy lockfiles FIRST so this layer is cached unless deps change
COPY pyproject.toml uv.lock ./
COPY package.json package-lock.json ./

# Install Python deps (Populates global UV_CACHE_DIR)
RUN uv sync --frozen --no-install-project

# Install Node deps & BACK THEM UP
# This backup allows us to restore node_modules after the source code mount hides them
RUN npm install && \
    mkdir -p /opt/backup && \
    cp -r node_modules /opt/backup/node_modules

# 4. Copy Source (for CI; dev container mount overrides this)
COPY . .
```

#### 1.2 Create Initialization Script
**File**: `.devcontainer/init.sh`

Create the restore script that runs after source mount:

```bash
#!/bin/bash
set -e
echo "🚀 Starting Dev Container Initialization..."

# Restore Node Dependencies if missing (due to volume mount)
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules)" ]; then
    echo "📦 Restoring node_modules from image backup..."
    cp -r /opt/backup/node_modules .
else
    echo "✅ node_modules already exists. Skipping restore."
fi

# Sync to catch any drift
echo "🔄 Syncing Node dependencies..."
npm install
echo "🐍 Syncing Python Environment..."
uv sync

echo "✅ Dev Container Initialization Complete!"
```

#### 1.3 Update devcontainer.json Configuration
**File**: `.devcontainer/devcontainer.json`

Configure Docker-in-Docker, uv cache volume, and initialization:

```jsonc
{
  "name": "gRPC Full Stack",
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".."
  },
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {
      "enableNonRootDocker": "true"
    },
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers-extra/features/prettier:1": {},
    "ghcr.io/devcontainers-extra/features/apt-get-packages:1": {
      "packages": "jq,procps,vim,cloc"
    }
  },
  
  // Port forwarding for all services
  "forwardPorts": [4200, 8080, 50051],
  "portsAttributes": {
    "4200": { "label": "Angular Dev Server" },
    "8080": { "label": "Envoy Proxy (gRPC-Web)" },
    "50051": { "label": "gRPC Backend" }
  },
  
  // CRITICAL: Run restore script after source mount
  "postCreateCommand": "bash .devcontainer/init.sh",
  
  // Optimization: Keep uv cache as persistent volume
  "mounts": [
    "source=uv-cache,target=/opt/uv-cache,type=volume"
  ],
  
  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": "${containerWorkspaceFolder}/.venv/bin/python",
        "python.testing.pytestEnabled": true,
        "editor.insertSpaces": true,
        "editor.tabSize": 2
      },
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-toolsai.jupyter",
        "tamasfe.even-better-toml",
        "angular.ng-template",
        "zxh404.vscode-proto3"
      ]
    }
  }
}
```

#### 1.4 Add Python gRPC Dependencies
**File**: `pyproject.toml`

Add to dev dependencies:
```toml
[dependency-groups]
dev = [
    # ... existing ...
    "betterproto[compiler]>=2.0.0b7",
    "grpclib>=0.4.7",
]
```

#### 1.5 Create Root package.json for Node Dependencies
**File**: `package.json` (project root)

Create root-level package.json for Angular CLI and shared tooling:
```json
{
  "name": "rpc-stream-prototype",
  "version": "0.0.0",
  "private": true,
  "description": "gRPC streaming prototype with Angular frontend",
  "scripts": {
    "ng": "ng"
  },
  "dependencies": {},
  "devDependencies": {
    "@angular/cli": "^19.0.0"
  }
}
```

#### 1.6 Create package-lock.json
**File**: `package-lock.json`

Run `npm install` locally to generate lockfile, or create minimal lockfile structure.

#### 1.7 Create CI Build Image Workflow (The Builder)
**File**: `.github/workflows/build-image.yaml`

Triggers only on dependency changes, pushes to GHCR:

```yaml
name: Pre-build Dev Container

on:
  push:
    branches: [main]
    paths:
      - '.devcontainer/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - 'package.json'
      - 'package-lock.json'

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and Push Dev Container
        uses: devcontainers/ci@v0.3
        with:
          imageName: ghcr.io/${{ github.repository }}/devcontainer
          cacheFrom: ghcr.io/${{ github.repository }}/devcontainer
          push: always
```

#### 1.8 Update CI Workflow (The Runner)
**File**: `.github/workflows/ci.yaml`

Triggers on all changes, pulls cached image, never pushes:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Run CI in Dev Container
        uses: devcontainers/ci@v0.3
        with:
          imageName: ghcr.io/${{ github.repository }}/devcontainer
          # Use pre-built image from build-image workflow as cache
          cacheFrom: ghcr.io/${{ github.repository }}/devcontainer
          # NEVER push from CI checks - saves time
          push: never
          runCmd: |
            # Run Quality Checks
            ./scripts/check_quality.sh
            
            # Run Tests
            uv run pytest tests/unit tests/integration -v
```

### Verification Checklist
- [ ] `./scripts/check_quality.sh` passes
- [ ] `docker compose version` works inside container (DinD enabled)
- [ ] `node --version` shows Node.js installed
- [ ] `ng version` shows Angular CLI installed
- [ ] `python -c "import betterproto"` succeeds
- [ ] `python -c "import grpclib"` succeeds
- [ ] `node_modules/` is restored after container rebuild
- [ ] uv cache persists across container rebuilds (check `/opt/uv-cache`)
- [ ] Ports 4200, 8080, 50051 are configured for forwarding
- [ ] CI build-image workflow triggers only on dependency file changes
- [ ] CI workflow uses cached image (fast boot time)

---

## PR #2: Directory Layout & Boilerplate

**Goal**: Establish the complete project structure with minimal scaffolding. No business logic—just the skeleton that subsequent PRs will fill in.

### Tasks

#### 2.1 Create Proto Files with Stub Service
**Directory**: `protos/`

Create all three proto files as specified:

**File**: `protos/proposal.proto`
```protobuf
syntax = "proto3";
package proposal.v1;
import "google/protobuf/timestamp.proto";

enum ProposalStatus {
  STATUS_UNSPECIFIED = 0;
  PENDING = 1;
  APPROVED = 2;
  REJECTED = 3;
}

message Proposal {
  string proposal_id = 1;
  string text = 2;
  ProposalStatus status = 3;
  google.protobuf.Timestamp created_at = 4;
}
```

**File**: `protos/session.proto`
```protobuf
syntax = "proto3";
package proposal.v1;
import "proposal.proto";

message Session {
  string session_id = 1;
}

message SessionEvent {
  oneof event {
    Proposal request_created = 1;
    Proposal request_updated = 2;
  }
}
```

**File**: `protos/approval_service.proto`
```protobuf
syntax = "proto3";
package proposal.v1;
import "session.proto";
import "proposal.proto";

service ProposalService {
  rpc CreateSession (CreateSessionRequest) returns (Session);
  rpc GetSession (GetSessionRequest) returns (Session);
  rpc Subscribe (SubscribeRequest) returns (stream SessionEvent);
  rpc SubmitProposal (SubmitProposalPayload) returns (Proposal);
  rpc SubmitDecision (SubmitDecisionPayload) returns (Proposal);
}

message CreateSessionRequest {}
message GetSessionRequest { string session_id = 1; }
message SubscribeRequest { string session_id = 1; string client_id = 2; }
message SubmitProposalPayload { string session_id = 1; string text = 2; }
message SubmitDecisionPayload { string session_id = 1; string proposal_id = 2; bool approved = 3; }
```

#### 2.2 Create Proto Generation Script
**File**: `scripts/gen_protos.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="$REPO_ROOT/protos"
PYTHON_OUT="$REPO_ROOT/rpc_stream_prototype/generated"

# Clean and recreate output directory
rm -rf "$PYTHON_OUT"
mkdir -p "$PYTHON_OUT/approval/v1"

# Generate Python code with betterproto
python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  -I "$(python -c 'import grpc_tools; print(grpc_tools.__path__[0])')/_proto" \
  --python_betterproto_out="$PYTHON_OUT/approval/v1" \
  "$PROTO_DIR"/*.proto

# Create __init__.py files
touch "$PYTHON_OUT/__init__.py"
touch "$PYTHON_OUT/approval/__init__.py"

echo "✅ Proto generation complete: $PYTHON_OUT"
```

#### 2.3 Restructure Python Package
**Directory**: `rpc_stream_prototype/`

Create the target structure (move/delete existing files as needed):

```
rpc_stream_prototype/
├── __init__.py
├── backend/
│   ├── __init__.py
│   ├── main.py              # Entry point (stub: prints "Server starting...")
│   └── services/
│       └── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py              # Entry point (stub: prints "CLI starting...")
│   └── ui/
│       └── __init__.py
├── generated/               # Created by gen_protos.sh
│   └── approval/
│       └── v1/
└── shared/                  # Shared utilities (logging, etc.)
    ├── __init__.py
    └── logging_config.py    # Move existing logging_config.py here
```

**File**: `rpc_stream_prototype/backend/main.py` (stub)
```python
"""Backend server entry point."""
import asyncio

async def serve() -> None:
    """Start the gRPC server."""
    print("Server starting on port 50051...")
    # Stub: actual implementation in PR #3
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(serve())
```

**File**: `rpc_stream_prototype/cli/main.py` (stub)
```python
"""CLI entry point."""
import typer

app = typer.Typer(help="Proposer CLI for real-time approval workflow")

@app.command()
def start():
    """Start a new proposal session."""
    print("CLI stub: start session")

@app.command()
def join(session_id: str):
    """Join an existing session."""
    print(f"CLI stub: join session {session_id}")

if __name__ == "__main__":
    app()
```

#### 2.4 Update pyproject.toml Entry Points
**File**: `pyproject.toml`

```toml
[project.scripts]
rpc-server = "rpc_stream_prototype.backend.main:serve"
rpc-cli = "rpc_stream_prototype.cli.main:app"
```

#### 2.5 Create Angular Application Scaffold
**Directory**: `frontend/`

Run Angular CLI to create the application:
```bash
cd /workspaces/rpc-stream-prototype
ng new frontend --routing --style=scss --skip-git --package-manager=npm
```

Then add required dependencies:
```bash
cd frontend
npm install @angular/material @angular/cdk
npm install @connectrpc/connect @connectrpc/connect-web @bufbuild/protobuf
```

Update `angular.json` to configure `ng serve` with poll option for Docker/WSL compatibility.

#### 2.6 Create Docker Compose Configuration
**File**: `docker-compose.yaml`

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    ports:
      - "50051:50051"
    volumes:
      - ./rpc_stream_prototype:/app/rpc_stream_prototype:cached
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
      - LOG_FILE=/app/logs/coordination-service.log
    command: >
      watchfiles
      --filter python
      "python -m rpc_stream_prototype.backend.main"
      /app/rpc_stream_prototype

  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/frontend.Dockerfile
    ports:
      - "4200:4200"
    volumes:
      - ./frontend:/app:cached
      - /app/node_modules
    command: ng serve --host 0.0.0.0 --poll 2000

  envoy:
    image: envoyproxy/envoy:v1.26-latest
    ports:
      - "8080:8080"
    volumes:
      - ./envoy/envoy.yaml:/etc/envoy/envoy.yaml:ro
    depends_on:
      - backend
```

#### 2.7 Create Dockerfiles
**File**: `docker/backend.Dockerfile`

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source (for initial build; volume mount overrides in dev)
COPY rpc_stream_prototype/ ./rpc_stream_prototype/

# Install watchfiles for hot-reload
RUN uv add watchfiles

EXPOSE 50051
```

**File**: `docker/frontend.Dockerfile`

```dockerfile
FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source (for initial build; volume mount overrides in dev)
COPY . .

EXPOSE 4200
```

#### 2.8 Create Envoy Configuration
**File**: `envoy/envoy.yaml`

```yaml
admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 9901

static_resources:
  listeners:
    - name: listener_0
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8080
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                codec_type: auto
                stat_prefix: ingress_http
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: local_service
                      domains: ["*"]
                      routes:
                        - match:
                            prefix: "/"
                          route:
                            cluster: grpc_service
                            timeout: 0s
                            max_stream_duration:
                              grpc_timeout_header_max: 0s
                      cors:
                        allow_origin_string_match:
                          - prefix: "*"
                        allow_methods: GET, PUT, DELETE, POST, OPTIONS
                        allow_headers: keep-alive,user-agent,cache-control,content-type,content-transfer-encoding,x-accept-content-transfer-encoding,x-accept-response-streaming,x-user-agent,x-grpc-web,grpc-timeout
                        expose_headers: grpc-status,grpc-message
                        max_age: "1728000"
                http_filters:
                  - name: envoy.filters.http.grpc_web
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.grpc_web.v3.GrpcWeb
                  - name: envoy.filters.http.cors
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.cors.v3.Cors
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: grpc_service
      connect_timeout: 0.25s
      type: logical_dns
      http2_protocol_options: {}
      lb_policy: round_robin
      load_assignment:
        cluster_name: grpc_service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: backend
                      port_value: 50051
```

#### 2.9 Create logs Directory with .gitkeep
**Directory**: `logs/`

```bash
mkdir -p logs
touch logs/.gitkeep
echo "*.log" >> logs/.gitignore
```

### Verification Checklist
- [ ] `./scripts/check_quality.sh` passes
- [ ] `./scripts/gen_protos.sh` generates Python code in `rpc_stream_prototype/generated/`
- [ ] `python -c "from rpc_stream_prototype.generated.proposal.v1 import approval_service"` succeeds
- [ ] `docker compose build` completes successfully
- [ ] `docker compose up` starts all three services (backend, frontend, envoy)
- [ ] Backend stub prints "Server starting..." in logs
- [ ] Frontend `ng serve` is accessible at http://localhost:4200
- [ ] Envoy is listening on port 8080

---

## PR #3: Server Implementation

**Goal**: Complete backend implementation with all gRPC service methods, in-memory storage, logging, and tests.

### Architecture

```
rpc_stream_prototype/backend/
├── main.py                    # Server entry point
├── services/
│   ├── __init__.py
│   └── proposal_service.py    # ProposalServiceBase implementation
├── storage/
│   ├── __init__.py
│   ├── repository.py          # SessionRepository interface
│   └── memory_store.py        # In-memory implementation
├── models/
│   ├── __init__.py
│   └── domain.py              # Internal domain models
└── events/
    ├── __init__.py
    └── broadcaster.py         # Event broadcasting to subscribers
```

### Tasks

#### 3.1 Create Domain Models
**File**: `rpc_stream_prototype/backend/models/domain.py`

Implement domain models with:
- `ProposalStatus` enum: PENDING, APPROVED, REJECTED
- `Proposal` dataclass: proposal_id, session_id, text, status, created_at; factory method `create()`
- `Session` dataclass: session_id, requests list; factory method `create()`, helper `get_pending_requests()`

#### 3.2 Create Repository Interface and In-Memory Implementation
**File**: `rpc_stream_prototype/backend/storage/repository.py`

Define `SessionRepository` ABC with methods:
- `create_session() -> Session`
- `get_session(session_id) -> Optional[Session]`
- `add_request(session_id, request) -> Proposal`
- `update_request(session_id, proposal_id, approved) -> Optional[Proposal]`

**File**: `rpc_stream_prototype/backend/storage/memory_store.py`

Implement `InMemorySessionRepository` with thread-safe access using `asyncio.Lock`.

#### 3.3 Create Event Broadcaster
**File**: `rpc_stream_prototype/backend/events/broadcaster.py`

Implement `EventBroadcaster` class with:
- `subscribe(session_id) -> asyncio.Queue` - returns queue for receiving events
- `unsubscribe(session_id, queue)` - removes subscriber
- `broadcast(event)` - sends event to all session subscribers

@dataclass
class SessionEvent:
    session_id: str
    event_type: str  # "request_created" | "request_updated"
    payload: dict

class EventBroadcaster:
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
    
    async def subscribe(self, session_id: str) -> asyncio.Queue:
        """Subscribe to events for a session. Returns a queue to receive events."""
        ...
    
    async def unsubscribe(self, session_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from session events."""
        ...
    
    async def broadcast(self, event: SessionEvent) -> None:
        """Broadcast an event to all subscribers of the session."""
        ...
```

#### 3.4 Implement ProposalService
**File**: `rpc_stream_prototype/backend/services/proposal_service.py`

Implement all RPC methods:

| Method | Type | Behavior | FR Coverage |
|--------|------|----------|-------------|
| `CreateSession` | Unary | Generate UUID, store session, return Session | FR-001, FR-002 |
| `GetSession` | Unary | Lookup by ID, return Session or raise NOT_FOUND | FR-002 |
| `Subscribe` | Server-Stream | Replay history, then stream new events | FR-003, FR-004, FR-005, FR-006 |
| `SubmitProposal` | Unary | Validate, create request, broadcast, return request | FR-004, FR-006a |
| `SubmitDecision` | Unary | Validate, update status, broadcast, return request | FR-005 |

#### 3.5 Implement Logging
**File**: `rpc_stream_prototype/backend/logging.py`

Configure dual logging:
- INFO level → stdout (NFR-001, NFR-002)
- DEBUG/VERBOSE level → file at `LOG_FILE` env var (NFR-003, NFR-004)

Log events:
- Client connections/disconnections
- Requests received
- Decisions made
- Internal state transitions (file only)

#### 3.6 Update Server Entry Point
**File**: `rpc_stream_prototype/backend/main.py`

```python
import asyncio
from grpclib.server import Server
from rpc_stream_prototype.backend.services.approval_service import ProposalServiceImpl
from rpc_stream_prototype.backend.storage.memory_store import InMemorySessionRepository
from rpc_stream_prototype.backend.events.broadcaster import EventBroadcaster
from rpc_stream_prototype.backend.logging import configure_logging

async def serve() -> None:
    configure_logging()
    
    repository = InMemorySessionRepository()
    broadcaster = EventBroadcaster()
    service = ProposalServiceImpl(repository, broadcaster)
    
    server = Server([service])
    await server.start("0.0.0.0", 50051)
    print("Server started on port 50051")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(serve())
```

#### 3.7 Create Shared Test Fixtures
**Directory**: `tests/fixtures/`

Per Constitution Principle IV (Classicist Testing), create high-fidelity fakes as shared fixtures:

| Fixture File | Purpose |
|--------------|---------|
| `fake_repository.py` | In-memory session repository for isolated unit tests |
| `fake_broadcaster.py` | Event broadcaster that records events for assertion |

These fakes MUST be reusable across all backend unit tests.

#### 3.8 Write Unit Tests
**Directory**: `tests/unit/backend/`

| Test File | Coverage |
|-----------|----------|
| `test_domain.py` | Domain model creation, state transitions |
| `test_memory_store.py` | Repository operations, concurrency |
| `test_broadcaster.py` | Subscribe/unsubscribe, event delivery |
| `test_proposal_service.py` | All RPC methods, error cases (uses shared fakes from `tests/fixtures/`) |

#### 3.9 Write Integration Tests
**Directory**: `tests/integration/`

| Test File | Coverage |
|-----------|----------|
| `test_server_e2e.py` | Full server startup, gRPC calls, streaming |

**Test Scenarios**:
1. Create session → returns valid UUID
2. Get non-existent session → raises NOT_FOUND
3. Submit request → broadcasts to subscribers
4. Submit decision → updates status, broadcasts
5. Subscribe → receives history replay + live events
6. Concurrent requests → queued FIFO (FR-006a)

### Verification Checklist
- [ ] `./scripts/check_quality.sh` passes
- [ ] Shared fakes exist in `tests/fixtures/`
- [ ] All unit tests pass: `pytest tests/unit/backend/`
- [ ] Integration tests pass: `pytest tests/integration/`
- [ ] Server starts: `docker compose up backend`
- [ ] Logs appear in stdout at INFO level (NFR-001, NFR-002)
- [ ] Verbose logs appear in `logs/coordination-service.log` (NFR-003, NFR-004)
- [ ] Can call `CreateSession` via grpcurl or test client

---

## PR #4: Proposer CLI Implementation

**Goal**: Complete CLI for Proposers to start/join sessions and submit proposals.

### Architecture

```
rpc_stream_prototype/cli/
├── main.py                # Typer app entry point
├── client/
│   ├── __init__.py
│   └── grpc_client.py     # betterproto client wrapper
├── ui/
│   ├── __init__.py
│   ├── console.py         # Rich console setup
│   ├── prompts.py         # Interactive prompts
│   └── display.py         # Status/proposal display
└── session/
    ├── __init__.py
    └── proposal_loop.py   # Main proposal submission loop
```

### Tasks

#### 4.1 Create gRPC Client Wrapper
**File**: `rpc_stream_prototype/cli/client/grpc_client.py`

```python
from grpclib.client import Channel
from rpc_stream_prototype.generated.proposal.v1 import ProposalServiceStub

class ProposalClient:
    def __init__(self, host: str = "localhost", port: int = 50051):
        self._channel = Channel(host, port)
        self._stub = ProposalServiceStub(self._channel)
    
    async def create_session(self) -> str:
        """Create a new session and return the session ID."""
        ...
    
    async def get_session(self, session_id: str) -> bool:
        """Check if session exists. Returns True if valid."""
        ...
    
    async def subscribe(self, session_id: str, client_id: str):
        """Subscribe to session events. Yields SessionEvent objects."""
        ...
    
    async def submit_proposal(self, session_id: str, text: str):
        """Submit a proposal for approval."""
        ...
    
    async def close(self):
        """Close the gRPC channel."""
        self._channel.close()
```

#### 4.2 Create Rich UI Components
**File**: `rpc_stream_prototype/cli/ui/display.py`

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def display_session_id(session_id: str) -> None:
    """Display session ID in a copyable format."""
    console.print(Panel(session_id, title="Session ID", subtitle="Share with Approvers"))

def display_waiting_state() -> None:
    """Show waiting for decision indicator."""
    console.print("[dim]Waiting for decision...[/dim]")

def display_proposal_sent(proposal_id: str, text: str) -> None:
    """Display confirmation that proposal was sent."""
    console.print(Panel(text, title=f"Proposal Sent: {proposal_id[:8]}...", border_style="blue"))

def display_decision_received(approved: bool) -> None:
    """Display received decision."""
    status = "[green]APPROVED[/green]" if approved else "[red]REJECTED[/red]"
    console.print(f"Decision received: {status}")
```

**File**: `rpc_stream_prototype/cli/ui/prompts.py`

```python
from rich.prompt import Prompt, Confirm

def prompt_session_action() -> str:
    """Ask user to start new or continue existing session."""
    return Prompt.ask(
        "What would you like to do?",
        choices=["start", "continue"],
        default="start"
    )

def prompt_session_id() -> str:
    """Ask user for session ID to continue."""
    return Prompt.ask("Enter Session ID")

def prompt_proposal_text() -> str:
    """Ask for proposal description."""
    return Prompt.ask("Enter your proposal")
```

#### 4.3 Implement Proposal Loop
**File**: `rpc_stream_prototype/cli/session/proposal_loop.py`

```python
import asyncio
from rpc_stream_prototype.cli.client.grpc_client import ProposalClient
from rpc_stream_prototype.cli.ui.display import display_waiting_state, display_proposal_sent, display_decision_received
from rpc_stream_prototype.cli.ui.prompts import prompt_proposal_text

async def run_proposal_loop(client: ProposalClient, session_id: str) -> None:
    """
    Main proposal submission loop.
    
    - Prompts for proposal text
    - Submits proposal to server
    - Waits for decision via subscription
    - Displays decision result
    - Loops until interrupted
    """
    client_id = str(uuid.uuid4())  # Unique identifier for this CLI instance
    
    while True:
        text = prompt_proposal_text()
        if not text.strip():
            continue
            
        proposal = await client.submit_proposal(session_id, text)
        display_proposal_sent(proposal.proposal_id, proposal.text)
        display_waiting_state()
        
        # Wait for decision via subscription
        async for event in client.subscribe(session_id, client_id):
            if event.proposal_updated and event.proposal_updated.proposal_id == proposal.proposal_id:
                approved = event.proposal_updated.status == ProposalStatus.APPROVED
                display_decision_received(approved)
                break
```

#### 4.4 Implement CLI Commands
**File**: `rpc_stream_prototype/cli/main.py`

```python
import asyncio
import typer
from rich.console import Console
from rpc_stream_prototype.cli.client.grpc_client import ProposalClient
from rpc_stream_prototype.cli.ui.display import display_session_id
from rpc_stream_prototype.cli.ui.prompts import prompt_session_action, prompt_session_id
from rpc_stream_prototype.cli.session.proposal_loop import run_proposal_loop

app = typer.Typer(help="Proposer CLI for real-time approval workflow")
console = Console()

@app.command()
def main(
    host: str = typer.Option("localhost", help="Backend server host"),
    port: int = typer.Option(50051, help="Backend server port")
):
    """Start the Proposer CLI."""
    asyncio.run(_main(host, port))

async def _main(host: str, port: int) -> None:
    client = ProposalClient(host, port)
    
    try:
        action = prompt_session_action()
        
        if action == "start":
            session_id = await client.create_session()
            display_session_id(session_id)
        else:
            session_id = prompt_session_id()
            if not await client.get_session(session_id):
                console.print("[red]Error: Session not found[/red]")
                return
            console.print(f"[green]Connected to session {session_id[:8]}...[/green]")
        
        await run_proposal_loop(client, session_id)
    
    except KeyboardInterrupt:
        console.print("\n[dim]Exiting...[/dim]")
    finally:
        await client.close()

if __name__ == "__main__":
    app()
```

#### 4.5 Create Shared Test Fixtures for CLI
**Directory**: `tests/fixtures/`

Per Constitution Principle IV, create high-fidelity fakes:

| Fixture File | Purpose |
|--------------|---------|
| `fake_proposal_client.py` | In-memory gRPC client that simulates server responses without network |

This fake MUST be reusable across CLI unit tests and avoid real network calls.

#### 4.6 Write Unit Tests
**Directory**: `tests/unit/cli/`

| Test File | Coverage |
|-----------|----------|
| `test_grpc_client.py` | Client wrapper methods (uses `FakeProposalClient` from `tests/fixtures/`) |
| `test_prompts.py` | Input validation, choice handling |
| `test_proposal_loop.py` | Proposal submission, decision flow (uses `FakeProposalClient`) |

#### 4.7 Write Integration Tests
**Directory**: `tests/integration/`

| Test File | Coverage |
|-----------|----------|
| `test_cli_e2e.py` | Full CLI flow with real server |

**Test Scenarios** (FR Coverage):
1. Start new session → displays UUID (FR-007, FR-009)
2. Continue existing session → connects successfully (FR-008)
3. Continue invalid session → shows error
4. Submit proposal → displays confirmation (FR-010)
5. Receive approved decision → displays APPROVED (FR-011)
6. Receive rejected decision → displays REJECTED (FR-011)
7. While waiting for decision → blocks input (FR-012)

### Verification Checklist
- [ ] `./scripts/check_quality.sh` passes
- [ ] Shared fakes exist in `tests/fixtures/fake_proposal_client.py`
- [ ] All unit tests pass: `pytest tests/unit/cli/`
- [ ] Integration tests pass: `pytest tests/integration/test_cli_e2e.py`
- [ ] CLI starts: `rpc-cli` or `python -m rpc_stream_prototype.cli.main`
- [ ] Can create session and see UUID
- [ ] Can continue existing session
- [ ] Proposals are submitted and confirmations displayed
- [ ] Decisions are received and displayed

---

## PR #5: Approver Web App Implementation

**Goal**: Complete web application for Approvers to join sessions, view proposals, and make approve/reject decisions.

### Architecture

```
frontend/src/app/
├── app.component.ts           # Root component
├── app.routes.ts              # Route configuration
├── core/
│   ├── services/
│   │   ├── approval.service.ts    # Connect-ES gRPC client
│   │   └── session-state.service.ts  # Session state management
│   └── models/
│       └── types.ts           # TypeScript interfaces
├── features/
│   ├── join-session/
│   │   ├── join-session.component.ts
│   │   └── join-session.component.html
│   └── session/
│       ├── session.component.ts
│       ├── session.component.html
│       ├── components/
│       │   ├── history-panel/
│       │   ├── decision-panel/
│       │   └── connection-status/
│       └── session.component.scss
└── shared/
    └── components/
        └── loading-spinner/
```

### Tasks

#### 5.1 Generate TypeScript from Protos
**File**: `frontend/buf.gen.yaml`

```yaml
version: v2
plugins:
  - local: protoc-gen-es
    out: src/generated
    opt: target=ts
  - local: protoc-gen-connect-es
    out: src/generated
    opt: target=ts
```

Add script to `frontend/package.json`:
```json
{
  "scripts": {
    "generate": "buf generate ../protos"
  }
}
```

#### 5.2 Create Approval Service
**File**: `frontend/src/app/core/services/approval.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { createGrpcWebTransport } from '@connectrpc/connect-web';
import { createClient } from '@connectrpc/connect';
import { ProposalService } from '../../../generated/proposal_service_connect';
import { Observable, Subject } from 'rxjs';
import { SessionEvent } from '../../../generated/session_pb';

@Injectable({ providedIn: 'root' })
export class ProposalServiceClient {
  private transport = createGrpcWebTransport({
    baseUrl: 'http://localhost:8080',
  });
  
  private client = createClient(ProposalService, this.transport);
  
  async getSession(sessionId: string): Promise<Session | null> {
    try {
      return await this.client.getSession({ sessionId });
    } catch {
      return null;
    }
  }
  
  subscribe(sessionId: string, clientId: string): Observable<SessionEvent> {
    const subject = new Subject<SessionEvent>();
    
    (async () => {
      try {
        for await (const event of this.client.subscribe({ sessionId, clientId })) {
          subject.next(event);
        }
      } catch (err) {
        subject.error(err);
      }
    })();
    
    return subject.asObservable();
  }
  
  async submitDecision(sessionId: string, proposalId: string, approved: boolean): Promise<Proposal> {
    return await this.client.submitDecision({ sessionId, proposalId, approved });
  }
}
```

#### 5.3 Create Session State Service
**File**: `frontend/src/app/core/services/session-state.service.ts`

```typescript
import { Injectable, signal, computed } from '@angular/core';
import { Proposal, ProposalStatus } from '../../../generated/proposal_pb';

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

@Injectable({ providedIn: 'root' })
export class SessionStateService {
  private _sessionId = signal<string | null>(null);
  private _proposals = signal<Proposal[]>([]);
  private _connectionState = signal<ConnectionState>('disconnected');
  
  // Public readable signals
  sessionId = this._sessionId.asReadonly();
  proposals = this._proposals.asReadonly();
  connectionState = this._connectionState.asReadonly();
  
  // Computed signals
  pendingProposals = computed(() => 
    this._proposals().filter(p => p.status === ProposalStatus.PENDING)
  );
  
  hasNoPendingProposals = computed(() => 
    this.pendingProposals().length === 0
  );
  
  // State mutations
  setSessionId(id: string) { this._sessionId.set(id); }
  setConnectionState(state: ConnectionState) { this._connectionState.set(state); }
  
  addProposal(proposal: Proposal) {
    this._proposals.update(proposals => [...proposals, proposal]);
  }
  
  updateProposal(proposal: Proposal) {
    this._proposals.update(proposals => 
      proposals.map(p => p.proposalId === proposal.proposalId ? proposal : p)
    );
  }
  
  reset() {
    this._sessionId.set(null);
    this._proposals.set([]);
    this._connectionState.set('disconnected');
  }
}
```

#### 5.4 Create Join Session Component
**File**: `frontend/src/app/features/join-session/join-session.component.ts`

```typescript
@Component({
  selector: 'app-join-session',
  templateUrl: './join-session.component.html',
  imports: [MatFormField, MatInput, MatButton, ReactiveFormsModule]
})
export class JoinSessionComponent {
  private router = inject(Router);
  private approvalService = inject(ProposalServiceClient);
  
  sessionIdControl = new FormControl('', [Validators.required, Validators.pattern(/^[0-9a-f-]{36}$/i)]);
  error = signal<string | null>(null);
  loading = signal(false);
  
  async onSubmit() {
    if (!this.sessionIdControl.valid) return;
    
    this.loading.set(true);
    this.error.set(null);
    
    const session = await this.approvalService.getSession(this.sessionIdControl.value!);
    
    if (session) {
      this.router.navigate(['/session', session.sessionId]);
    } else {
      this.error.set('Session not found. Please check the ID and try again.');
    }
    
    this.loading.set(false);
  }
}
```

#### 5.5 Create Session Component
**File**: `frontend/src/app/features/session/session.component.ts`

Main session view with:
- History panel showing all proposals/decisions
- Decision panel for pending proposals (Approve/Reject buttons)
- Connection status indicator
- Auto-reconnect logic

```typescript
@Component({
  selector: 'app-session',
  templateUrl: './session.component.html',
  imports: [HistoryPanelComponent, DecisionPanelComponent, ConnectionStatusComponent]
})
export class SessionComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private approvalService = inject(ProposalServiceClient);
  private sessionState = inject(SessionStateService);
  private destroyRef = inject(DestroyRef);
  
  ngOnInit() {
    const sessionId = this.route.snapshot.paramMap.get('id')!;
    this.sessionState.setSessionId(sessionId);
    this.connect(sessionId);
  }
  
  private connect(sessionId: string) {
    this.sessionState.setConnectionState('connecting');
    const clientId = crypto.randomUUID();
    
    this.approvalService.subscribe(sessionId, clientId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        retryWhen(errors => errors.pipe(
          tap(() => this.sessionState.setConnectionState('reconnecting')),
          delay(2000)
        ))
      )
      .subscribe({
        next: (event) => {
          this.sessionState.setConnectionState('connected');
          if (event.proposalCreated) {
            this.sessionState.addProposal(event.proposalCreated);
          } else if (event.proposalUpdated) {
            this.sessionState.updateProposal(event.proposalUpdated);
          }
        },
        error: () => this.sessionState.setConnectionState('disconnected')
      });
  }
}
```

#### 5.6 Create History Panel Component
**File**: `frontend/src/app/features/session/components/history-panel/history-panel.component.ts`

Display chronological list of proposals with status badges (Pending/Approved/Rejected).

#### 5.7 Create Decision Panel Component
**File**: `frontend/src/app/features/session/components/decision-panel/decision-panel.component.ts`

```typescript
@Component({
  selector: 'app-decision-panel',
  templateUrl: './decision-panel.component.html',
  imports: [MatButton, MatCard]
})
export class DecisionPanelComponent {
  private approvalService = inject(ProposalServiceClient);
  private sessionState = inject(SessionStateService);
  
  pendingProposals = this.sessionState.pendingProposals;
  
  async approve(proposalId: string) {
    await this.approvalService.submitDecision(
      this.sessionState.sessionId()!,
      proposalId,
      true
    );
  }
  
  async reject(proposalId: string) {
    await this.approvalService.submitDecision(
      this.sessionState.sessionId()!,
      proposalId,
      false
    );
  }
}
```

#### 5.8 Create Connection Status Component
**File**: `frontend/src/app/features/session/components/connection-status/connection-status.component.ts`

Display connection state with appropriate indicators:
- Connected: green dot
- Connecting/Reconnecting: spinner
- Disconnected: red warning

#### 5.9 Configure Routes
**File**: `frontend/src/app/app.routes.ts`

```typescript
export const routes: Routes = [
  { path: '', component: JoinSessionComponent },
  { path: 'session/:id', component: SessionComponent },
  { path: '**', redirectTo: '' }
];
```

#### 5.10 Configure Angular Material Theme
**File**: `frontend/src/styles.scss`

Import Angular Material theme and configure colors.

#### 5.11 Write Unit Tests
**Directory**: `frontend/src/app/`

| Test File | Coverage |
|-----------|----------|
| `core/services/approval.service.spec.ts` | gRPC client methods |
| `core/services/session-state.service.spec.ts` | State management |
| `features/join-session/join-session.component.spec.ts` | Form validation, navigation |
| `features/session/session.component.spec.ts` | Subscription, reconnection |
| `features/session/components/*.spec.ts` | Individual component behavior |

#### 5.12 Write E2E Tests
**Directory**: `frontend/e2e/`

Using Playwright or Cypress:

| Test File | Coverage |
|-----------|----------|
| `join-session.spec.ts` | Join flow, validation errors |
| `session-workflow.spec.ts` | Full proposal/decision flow |
| `reconnection.spec.ts` | Connection loss handling |

**Test Scenarios** (FR Coverage):
1. Load app → shows Session ID input (FR-013)
2. Enter invalid ID → shows error (FR-013)
3. Enter valid ID → navigates to session view (FR-014)
4. Session view shows history (FR-014)
5. Receive proposal → displays in decision panel (FR-015)
6. Click Approve → sends approved decision (FR-016)
7. Click Reject → sends rejected decision (FR-016)
8. After decision → proposal moves to history with status badge (FR-017)
9. No pending proposals → waiting state displayed (FR-018)
10. Connection lost → shows indicator (FR-019)
11. Auto-reconnect → shows reconnecting state (FR-020)

### Verification Checklist
- [ ] `./scripts/check_quality.sh` passes (Python code)
- [ ] All unit tests pass: `cd frontend && ng test`
- [ ] E2E tests pass: `cd frontend && ng e2e`
- [ ] App builds: `cd frontend && ng build`
- [ ] Can join session via UI
- [ ] Can see incoming proposals
- [ ] Can approve/reject proposals
- [ ] Real-time updates work (< 5 seconds per SC-001)
- [ ] History displays correctly (SC-002)
- [ ] Connection status shows correctly
- [ ] Auto-reconnect works

---

## Dependency Graph

```
PR #1 (Environment)
    │
    ▼ [rebuild devcontainer]
PR #2 (Boilerplate)
    │
    ├────────────┬────────────┐
    ▼            ▼            ▼
PR #3         PR #4         PR #5
(Server)    (requires 3)  (requires 3)
    │            │            │
    └────────────┴────────────┘
                 │
                 ▼
           Integration Testing
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| betterproto compatibility with Python 3.14 | Test in PR #1 before proceeding; fallback to grpcio if needed |
| gRPC-Web streaming through Envoy | Validate Envoy config early in PR #2 with simple echo test |
| Hot-reload not working in Docker | Test watchfiles + volume mounts in PR #2 isolation |
| Connect-ES TypeScript generation | Validate buf toolchain works in PR #2 |

---

## Success Metrics Validation

| Criterion | How to Validate | PR |
|-----------|-----------------|-----|
| SC-001 (5s latency) | Integration test with timestamps | PR #5 |
| SC-002 (chronological history) | Unit test + E2E test | PR #3, #5 |
| SC-003 (2min workflow) | Manual walkthrough timing | Final |
| SC-004 (10 requests) | Integration stress test | PR #3 |
| SC-005 (auto-update) | E2E test - no refresh | PR #5 |
| SC-006 (CLI feedback) | Unit tests for display functions | PR #4 |