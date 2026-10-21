from __future__ import annotations

import time
from collections import Counter
from uuid import UUID

from prefect import task
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import ArtifactFilter, FlowRunFilter

from flows.agentic_pr_verification import VerificationSpec
from flows.agentic_stack import digest
from flows.agentic_stack_policy import Batch, Group, publication_revision
from flows.agentic_stack_runtime import Runtime, collect, owner_alive, record


def verification_result(run_id: UUID, runtime: Runtime, spec: VerificationSpec) -> dict:
    with get_client(sync_client=True) as client:
        run = client.read_flow_run(run_id)
        if (
            run.state is None
            or not run.state.is_completed()
            or run.deployment_id != runtime.verification_id
            or run.deployment_version != runtime.source_sha
            or run.parameters != {"spec": spec.model_dump(mode="json")}
        ):
            raise ValueError(
                "Verification needs a completed run with the exact source and parameters"
            )
        records = client.read_artifacts(
            artifact_filter=ArtifactFilter(
                type={"any_": ["fastmcp-contribution-verification"]}
            ),
            flow_run_filter=FlowRunFilter(id={"any_": [run_id]}),
            limit=2,
        )
    if len(records) != 1 or not isinstance(records[0].data, dict):
        raise ValueError("Expected one contribution verification artifact")
    result = records[0].data
    if result.get("spec_sha256") != digest(spec.model_dump(mode="json")) or result.get(
        "spec"
    ) != spec.model_dump(mode="json"):
        raise ValueError("Verification artifact describes different inputs")
    return result


def summary(result: dict) -> dict:
    stages = {}
    for name in ("base", "head", "adjacent"):
        stage = result.get(name, {})
        stages[name] = {
            "status": stage.get("status", "not_run"),
            "counts": dict(Counter(case["state"] for case in stage.get("cases", []))),
            "failures": [
                case
                for case in stage.get("cases", [])
                if case["state"] in {"failure", "error"}
            ],
        }
    return {
        "run_id": result["run_id"],
        "pr_number": result["spec"]["pr_number"],
        "head_sha": result["spec"]["head_sha"],
        "baseline_sha": result.get("baseline_sha"),
        "status": result["status"],
        "tests": stages,
        "comparison": result.get("comparison", {}),
        "independent_probes": sorted(result["spec"]["probes"]),
        "limitations": result.get("limitations", []),
        "usage": result["usage"],
    }


@task(retries=2, retry_delay_seconds=[2, 5], persist_result=False)
def verify_existing(
    owner: UUID,
    batch: Batch,
    group: Group,
    runtime: Runtime,
    item: dict,
    probes: dict[str, str],
) -> dict:
    if runtime.verification_id is None:
        raise ValueError(
            "Existing contributions require a configured managed verification deployment"
        )
    evidence = item["evidence"]
    selected = {pr["number"] for pr in item["route"].get("pull_requests", [])}
    prs = [
        pr
        for pr in evidence["prs"]
        if pr["state"] == "open" and pr["number"] in selected
    ]
    if not 1 <= len(prs) <= 3:
        raise ValueError("Existing verification needs one to three open contributions")
    if probes and len(prs) != 1:
        raise ValueError("Independent probes require one selected open contribution")
    results = []
    for pr in prs:
        if pr["base_ref"] != group.branch:
            raise ValueError("Existing contribution targets a different release line")
        spec = VerificationSpec(
            issue_number=evidence["issue"]["number"],
            pr_number=pr["number"],
            head_sha=pr["head_sha"],
            trunk_sha=group.base_sha,
            trunk_ref=group.branch,
            evidence_revision=publication_revision(evidence),
            probes=probes,
        )
        owner_alive(owner, batch.expires_at)
        with get_client(sync_client=True) as client:
            deployment = client.read_deployment(runtime.verification_id)
            if (
                deployment.version != runtime.source_sha
                or deployment.work_pool_name != "managed"
            ):
                raise ValueError("Verification deployment changed or is not managed")
            run = client.create_flow_run_from_deployment(
                runtime.verification_id,
                parameters={"spec": spec.model_dump(mode="json")},
                idempotency_key=f"fastmcp-verify-{runtime.source_sha}-{digest(spec.model_dump(mode='json'))}",
            )
        record(
            owner,
            f"{batch.id}-pr-{pr['number']}-verification",
            {"run_id": str(run.id), "spec": spec.model_dump(mode="json")},
        )
        while True:
            owner_alive(owner, batch.expires_at)
            with get_client(sync_client=True) as client:
                run = client.read_flow_run(run.id)
            if run.state is not None and run.state.is_final():
                break
            time.sleep(5)
        results.append(
            summary(
                {"run_id": str(run.id), **verification_result(run.id, runtime, spec)}
            )
        )
    current = collect(evidence["issue"]["number"], group.branch)
    stale = publication_revision(current) != publication_revision(evidence)
    return {
        "issue_number": evidence["issue"]["number"],
        "assessment": item["assessment"],
        "route": item["route"],
        "verification": results,
        "status": "stale" if stale else "verification_recorded",
        "merge_ready": False,
        "next_step": "Refresh changed evidence"
        if stale
        else "Review executed tests and failures against the established contract; full-suite and composition checks remain separate",
    }
