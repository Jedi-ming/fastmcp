# Agentic maintenance

Experimental FastMCP maintenance automation for Prefect Cloud. This directory owns
the execution plans, deterministic controller, tests and deployment definitions.
It is an isolated Python 3.12 project; Prefect is not a FastMCP library dependency.
Cloud workers fetch an immutable commit from `PrefectHQ/fastmcp` and execute here.

## Review outputs

The first milestone is complete triage: collect evidence, assess it, execute the
appropriate verification, and return an actionable review queue. Fix stacks are a
later capability. Classification alone does not satisfy this milestone.

A manually selected batch contains at most six issues in two coherent groups.
`gh` collects existing labels, full issue discussion, all-state related PRs,
reviews and source revisions. Deterministic policy routes existing contributions,
claims, security reports and outstanding reproduction requests before model work.
It never writes labels. Existing automation retains ownership of its timers and
contribution gates.

The original intake remains an immutable artifact. Assessment receives a compact
view with full discussion text, event identities instead of repeated issue bodies,
and summarized successful checks. For open contributions it also receives bounded
current diffs and changes since the original reviewed commits. Moved heads stop
collection; missing patches and comparison limits are explicit. A stale review
does not establish a current defect, and diff inspection does not count as a test.
The assessor loads contribution-review skills; test-authoring guidance is reserved
for the reproduction, preparation and independent review roles.

Before starting another assessment, the controller looks up a durable fingerprint
index, falling back to the twelve most recent completed role runs for older
unindexed results. Reuse requires identical skills and projected inputs,
the same complete intake revision and active plan version, and a successful
non-operational decision. Only the raw snapshot hash, which includes collection
time, is excluded from comparison. Revision hashes ignore repository-wide counts,
size and activity timestamps embedded in cross-reference events; those remain in
the retained raw evidence. Changed contribution history, revisions, labels or
skills invalidate reuse. Reused assessments retain provenance and add zero new model
usage to the batch; historical usage is not counted again.

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

Existing-contribution assessments now dispatch to `cloud-contribution-verification`.
The verifier fetches immutable commits, derives changed test modules from their
merge base, and runs them on both the pinned current release target and proposed
head. Optional independent
probes run on both as well. Neighboring test modules run on the head. The repository
lockfile is installed without re-resolution; JUnit cases distinguish assertion
failures, setup errors, skips and missing tests. Test processes receive a separate
home and an explicit environment without controller credentials; this is not an
operating-system sandbox. Each command has a timeout that terminates its process
group.

Results retain the source revisions, probe source, commands, exit codes and test
transitions. The controller checks deployment version and exact inputs before
accepting an artifact, rechecks contribution evidence afterward, and retains stale
results as historical evidence. Matching requests reuse the same verification run.
This deterministic stage uses no model tokens. Provider compute cost remains
unknown. Passing contributor tests is not a merge recommendation: contract review,
current-branch composition and full-suite/static checks remain separate evidence.

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

This registers `cloud-stack-batch`, `cloud-stack-validation`, and
`cloud-contribution-verification` in the managed pool, with no schedules. The
publisher loads the existing Cloud Secret block
`fastmcp-triage-gh-token`. Agent roles receive no GitHub write credential.

Managed execution accepts only its supported image tags, not arbitrary patch
version tags. The deployment uses its supported Python 3.12 image and installs
the pinned Prefect version and FastAPI compatibility constraint before pull steps.

Prepare a batch matching `flows.agentic_stack_policy.Batch` and runtime inputs
matching `flows.agentic_stack_runtime.Runtime`. Runtime inputs name the four
published role flow/version IDs, validator deployment ID, contribution verification
deployment ID (`verification_id`) and controller source SHA. Once the named batch
and its external effects are approved:

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
