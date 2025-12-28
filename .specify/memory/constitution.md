<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version change: N/A → 1.0.0 (initial ratification)

Added sections:
- Core Principles (4 principles)
- Development Tooling
- Quality Gates
- Governance

Templates validation:
- ✅ plan-template.md: Compatible (Constitution Check section present)
- ✅ spec-template.md: Compatible (no direct constitution references)
- ✅ tasks-template.md: Compatible (test organization aligns with Classicist approach)

Follow-up TODOs: None
================================================================================
-->

# RPC Stream Prototype Constitution

## Purpose

This codebase is a **learning exercise** to understand bidirectional streaming in gRPC from both server and client perspectives.

**Primary Goal**: Simplicity and understandability.

**Explicit Non-Goal**: Production-grade robustness, especially when it introduces additional complexity.

## Core Principles

### I. Simplicity First

All design decisions MUST prioritize clarity and ease of understanding over production hardening.

- Code MUST be written to teach and illustrate gRPC streaming concepts
- Abstractions SHOULD only be introduced when they improve comprehension
- Complex error handling, retry logic, or resilience patterns MUST NOT be added unless they directly serve the learning objective
- When choosing between a "correct" complex solution and a "good enough" simple solution, prefer simplicity

**Rationale**: This is a prototype for learning. Complexity obscures the core concepts being studied.

### II. Dev Container-Managed System Dependencies

System-level dependencies MUST be managed via dev container configuration.

- All system packages, tools, and runtime dependencies MUST be declared in `.devcontainer/devcontainer.json` or related Dockerfile
- Developers MUST NOT require manual system installation steps beyond opening the dev container
- The dev container MUST provide a reproducible, consistent development environment

**Rationale**: Ensures any developer can clone and immediately work without environment setup friction.

### III. UV-Managed Python Dependencies

Python dependencies MUST be managed via `uv`.

- All Python packages MUST be declared in `pyproject.toml`
- Dependency installation MUST use `uv sync`
- Script execution MUST use `uv run`
- Direct `pip install` commands are PROHIBITED in development workflows

**Rationale**: uv provides fast, reproducible dependency resolution with lockfile support.

### IV. Classicist Unit Testing

Unit tests MUST follow the "Classicist" (Detroit School) approach with the following dependency hierarchy:

1. **Real Implementation (Preferred)**: Use actual dependency code whenever possible
2. **High-Fidelity Fakes**: Use lightweight, in-memory implementations for slow or I/O-bound dependencies (databases, network calls)
   - Fakes MUST be implemented as shared, reusable components (e.g., `FakePaymentGateway` class)
   - Fakes MUST be located in `tests/fixtures/` and used consistently across the test suite
   - Ad-hoc or inline fakes for individual tests are PROHIBITED
3. **Mocks/Stubs (Last Resort)**: Use ONLY for non-deterministic behavior or error states that cannot be reproduced with Fakes

**Verification Style**: Tests MUST use State-Based Verification (checking return values or state changes) rather than Interaction-Based Verification (checking which methods were called).

**Rationale**: Classicist testing produces more resilient tests that verify behavior rather than implementation details.

## Development Tooling

- **Quality Checks**: Agents MUST execute `./scripts/check_quality.sh` before considering code complete
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Type Checking**: Pyright in strict mode
- **Testing**: pytest with `tests/` directory structure

## Quality Gates

Before any code is considered complete:

1. `./scripts/check_quality.sh` MUST pass with zero errors
2. All new functionality MUST have corresponding unit tests
3. Tests MUST follow the Classicist hierarchy (real → fake → mock)
4. Shared fakes MUST be placed in `tests/fixtures/`

## Governance

This constitution supersedes all other development practices for this repository.

- All code contributions MUST comply with these principles
- Amendments require updating this document with version increment
- Version follows semantic versioning: MAJOR (principle changes), MINOR (new sections), PATCH (clarifications)

**Version**: 1.0.0 | **Ratified**: 2025-12-28 | **Last Amended**: 2025-12-28
