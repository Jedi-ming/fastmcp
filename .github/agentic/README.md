# Agentic maintenance

Experimental FastMCP maintenance automation for Prefect Cloud. This directory owns
the execution plans, deterministic controller, tests and deployment definitions.
It is an isolated Python 3.12 project; Prefect is not a FastMCP library dependency.
Cloud workers fetch an immutable commit from `PrefectHQ/fastmcp` and execute here.

## Review outputs

A manually selected batch contains at most six issues in two coherent groups.
`gh` collects existing labels, full issue discussion, all-state related PRs,
reviews and source revisions. Deterministic policy routes existing contributions,
claims, security reports and outstanding reproduction requests before model work.
It never writes labels. Existing automation retains ownership of its timers and
contribution gates.

Explicit Luna roles use complete repository skills pinned to the source revision:
assessment, reproduction, preparation and independent review. Each role has one
attempt and a 180-second platform limit. The batch allows one repair round and a
two-hour window. Haiku is configured as a comparison candidate, not an automatic
fallback. Missing telemetry remains unknown; these are execution bounds, not a
hard token or dollar cap.

Qualified patches become two- or three-layer draft GitHub Stacks. Each layer is
validated on its actual parent with the full FastMCP suite and static checks.
Immutable Prefect artifacts retain the exact commits, patches, credit and review.
Publication rechecks ownership, issue history, holds and branch heads; uncertain
writes reconcile with existing GitHub objects. A single useful patch is retained
without manufacturing a second layer. Other results are grouped as existing-work
reviews, evidence, pruning proposals, maintainer decisions or operational failures.

Fork PRs are reviewed in place. Adoption and supersession require a maintainer's
decision, with original authorship and issue credit preserved. Closed PRs are
evidence: distinguish assignment-gate closure from explicit maintainer rejection
or supersession. See [maintenance history](docs/fastmcp-maintenance-history.md) and
[architecture decisions](docs/agentic-stack-architecture.md).

## Local verification

From this directory:

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest -q
```

The tests use temporary Git repositories, a local HTTP fault server and a real
temporary Prefect server. They need `git`, `gh` and `jq` on PATH. They do not need
Cloud credentials and do not publish GitHub objects. The separate CI workflow
runs these checks without adding automation dependencies to the library suite.

## Cloud setup and manual operation

Use an authenticated Prefect CLI profile or `PREFECT_API_KEY`. Set
`PREFECT_API_URL` to the intended Cloud workspace URL. The launcher rejects
self-hosted URLs. Configure that workspace's provider connection ID and explicit
models in `workflows/stack-models.json`, then regenerate the plans:

```sh
uv run python -m flows.agentic_stack_plans
bash scripts/agentic_stack.sh validate
```

Publish the four new role plans through the Agentic Workflows tooling. Registration
requires a clean checkout at a commit already available in `PrefectHQ/fastmcp`:

```sh
bash scripts/agentic_stack.sh register
```

This registers only `cloud-stack-batch` and `cloud-stack-validation` in the managed
pool, with no schedules. The publisher loads the existing Cloud Secret block
`fastmcp-triage-gh-token`. Agent roles receive no GitHub write credential.

Prepare a batch matching `flows.agentic_stack_policy.Batch` and runtime inputs
matching `flows.agentic_stack_runtime.Runtime`. Runtime inputs name the four
published role flow/version IDs, validator deployment ID and controller source
SHA. Once the named batch and its external effects are approved:

```sh
bash scripts/agentic_stack.sh run /absolute/path/batch.json /absolute/path/runtime.json CONTROLLER_DEPLOYMENT_ID
bash scripts/agentic_stack.sh results CONTROLLER_RUN_ID
```

Registration is not a successful trial. This implementation has not yet produced
a live stack. Before unattended use, verify the managed runtime, actual PR/stack
readback, cancellation and observed token usage on a bounded batch. Cancellation
stops further publication; an already-started child can run to its own limit.
Public comments, closures, assignments, ready transitions, merges and recurring
schedules are outside this initial automation's authority.
