from copy import deepcopy

from flows.agentic_review_queue import plain, review_markdown


def test_queue_distinguishes_regression_operational_failure_and_stale_evidence():
    result = {
        "batch_id": "trial",
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "bins": {
            "existing_review": [
                {
                    "issue_number": 1,
                    "assessment": {"reason": "Existing contribution"},
                    "route": {"pull_requests": [{"number": 2, "held": True}]},
                    "verification": [
                        {
                            "pr_number": 2,
                            "head_sha": "a" * 40,
                            "baseline_sha": "b" * 40,
                            "run_id": "run",
                            "status": "verification_recorded",
                            "comparison": {
                                "fixed_tests": ["reported_bug"],
                                "regressed_tests": ["neighbor"],
                            },
                        }
                    ],
                }
            ]
        },
    }
    markdown = review_markdown(result)
    assert "A regression was reproduced" in markdown
    assert "Contribution holds retained" in markdown
    assert "1 fail-to-pass cases; 1 pass-to-fail cases" in markdown
    changed = deepcopy(result)
    item = changed["bins"]["existing_review"][0]
    item["status"] = "stale"
    item["verification"][0]["status"] = "environment_failure"
    markdown = review_markdown(changed)
    assert "Evidence changed" in markdown
    assert "Verification could not complete" in markdown
    assert "A regression was reproduced" not in markdown
    assert "Observed input tokens: 0" in markdown


def test_model_text_cannot_create_links_or_override_queue_formatting():
    assert (
        plain("[open account settings](https://attacker.example)")
        == r"\[open account settings\]\(https://attacker\.example\)"
    )
    assert plain(None) == "unknown"
