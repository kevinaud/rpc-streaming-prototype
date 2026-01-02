<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version change: 1.0.0 → 1.1.0 (new section added)

Modified sections:
- (none)

Added sections:
- Frontend Architecture & Standards (6 rules for Angular development)

Removed sections:
- (none)

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

## Frontend Architecture & Standards

This section defines mandatory constraints for all Angular code in `frontend/`.

### I. Modern Lifecycle Management

Components and services MUST use `DestroyRef` and `takeUntilDestroyed` for cleanup logic.

- Implementing the `OnDestroy` interface is PROHIBITED unless required for external library interoperability
- Manual boolean flags (e.g., `isDestroyed`, `isAlive`) to track component lifecycle are PROHIBITED
- Cleanup callbacks MUST be registered via `this.destroyRef.onDestroy(() => ...)`

```typescript
// ❌ PROHIBITED
class MyComp implements OnDestroy {
  isAlive = true;
  ngOnDestroy() { this.isAlive = false; }
}

// ✅ REQUIRED
class MyComp {
  private readonly destroyRef = inject(DestroyRef);

  constructor() {
    this.destroyRef.onDestroy(() => {
      // cleanup logic here
    });
  }
}
```

**Rationale**: DestroyRef provides a declarative, injection-based lifecycle that eliminates boilerplate and prevents missed cleanup.

### II. Dependency Injection Strategy

All dependencies MUST be obtained using the `inject()` function.

- Constructor-based dependency injection is PROHIBITED
- Dependencies SHOULD be declared as `private readonly` class fields

```typescript
// ❌ PROHIBITED
constructor(private service: UserService) {}

// ✅ REQUIRED
private readonly userService = inject(UserService);
```

**Rationale**: `inject()` enables safer field initialization, clearer type inference, and avoids constructor parameter ordering issues.

### III. Signal State Encapsulation

State services MUST follow the "Private Writable / Public Readonly" pattern.

- `WritableSignal` instances MUST be private
- Public state MUST be exposed as `Signal<T>` (readonly) using `.asReadonly()`
- Direct mutation of state from outside the owning service is PROHIBITED

```typescript
// ✅ REQUIRED PATTERN
private readonly _currentUser = signal<User | null>(null);
readonly currentUser = this._currentUser.asReadonly();
```

**Rationale**: Enforces unidirectional data flow and prevents accidental state corruption from consumer components.

### IV. Computed Signal Type Safety

Computed signals that may return `null` or `undefined` MUST have explicit generic type annotations.

- Relying on type inference for nullable return values is PROHIBITED
- The generic type MUST document the nullability intent

```typescript
// ❌ PROHIBITED (relies on inference for nullable)
readonly activeItem = computed(() => findItem() || null);

// ✅ REQUIRED
readonly activeItem = computed<Item | undefined>(() => this.items().find(i => i.active));
```

**Rationale**: Explicit types prevent "Type 'null' is not assignable to 'undefined'" errors and document API contracts.

### V. Template Control Flow

Components MUST use Angular's built-in control flow syntax (`@if`, `@for`, `@switch`).

- Structural directives (`*ngIf`, `*ngFor`, `*ngSwitch`) are PROHIBITED
- Importing `CommonModule` solely for structural directives is PROHIBITED

**Rationale**: Built-in control flow is more performant, requires no imports, and is the forward-looking Angular standard.

### VI. Streaming Data Handling

When consuming `AsyncIterable` (gRPC streams) or Observables in components:

- Cancellation MUST be handled via `DestroyRef` or an `AbortController` tied to `DestroyRef`
- Manual boolean flags to break async loops are PROHIBITED
- For `AsyncIterable`, pass an `AbortSignal` or check `destroyRef` to exit iteration

```typescript
// ✅ REQUIRED PATTERN for AsyncIterable
private readonly destroyRef = inject(DestroyRef);

async consumeStream(stream: AsyncIterable<Event>) {
  const abortController = new AbortController();
  this.destroyRef.onDestroy(() => abortController.abort());

  for await (const event of stream) {
    if (abortController.signal.aborted) break;
    // process event
  }
}
```

**Rationale**: Ties stream lifecycle to component lifecycle automatically, preventing memory leaks and orphaned subscriptions.

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

**Version**: 1.1.0 | **Ratified**: 2025-12-28 | **Last Amended**: 2025-12-30
