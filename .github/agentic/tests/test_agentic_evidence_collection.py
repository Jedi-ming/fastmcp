import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAKE_GH = """\
import json, re, sys
from urllib.parse import parse_qsl

routes = json.load(open(sys.argv[1]))
args = sys.argv[2:]
assert args[0] == "api"
fields, positional, rest = {}, [], iter(args[1:])
for arg in rest:
    if arg == "-f":
        name, _, value = next(rest).partition("=")
        fields[name] = value
    elif arg.startswith("-"):
        next(rest)
    else:
        positional.append(arg)
endpoint = positional[0]
path, _, query = endpoint.partition("?")
if path == "search/issues":
    key = "search:" + fields["q"]
else:
    key = path
    if dict(parse_qsl(query)).get("page", "1") != "1":
        print("[]")
        sys.exit(0)
if key not in routes:
    print("unrouted " + key, file=sys.stderr)
    sys.exit(1)
print(json.dumps(routes[key]))
"""


def pr(number, body):
    return {
        "number": number,
        "title": f"Change {number}",
        "body": body,
        "state": "open",
        "draft": False,
        "merged": False,
        "html_url": f"https://github.com/PrefectHQ/fastmcp/pull/{number}",
        "updated_at": "2026-10-21T00:00:00Z",
        "user": {"id": 1, "login": "contributor", "type": "User"},
        "labels": [],
        "base": {"ref": "main", "sha": "b" * 40},
        "head": {"ref": "fix", "sha": "c" * 40, "repo": {"full_name": "a/fastmcp"}},
    }


def test_numeric_search_ignores_prs_that_only_mention_the_number(tmp_path):
    repo = "repos/PrefectHQ/fastmcp"
    linked = pr(9001, "Fixes #2026")
    unrelated = [
        {"number": n, "body": f"Released 2026-10-{n % 28 + 1:02d}"}
        for n in range(100, 140)
    ]
    routes = {
        f"{repo}/issues/2026": {
            "number": 2026,
            "title": "ProxyClient double-serializes objects",
            "body": "",
            "state": "open",
            "html_url": "https://github.com/PrefectHQ/fastmcp/issues/2026",
            "updated_at": "2026-10-21T00:00:00Z",
            "author_association": "NONE",
            "user": {"id": 2, "login": "reporter", "type": "User"},
            "assignees": [],
            "labels": [],
            "pull_request": None,
        },
        f"{repo}/issues/2026/comments": [],
        f"{repo}/issues/2026/timeline": [],
        f"{repo}/labels": [],
        f"{repo}/stacks": [],
        f"{repo}/commits/main": {"sha": "b" * 40},
        "search:repo:PrefectHQ/fastmcp is:pr 2026 in:body": {
            "total_count": len(unrelated) + 1,
            "incomplete_results": False,
            "items": [*unrelated, {"number": 9001, "body": "Fixes #2026"}],
        },
        'search:repo:PrefectHQ/fastmcp is:pr "ProxyClient" "serializes" "objects" "double"': {
            "total_count": 0,
            "incomplete_results": False,
            "items": [],
        },
        f"{repo}/pulls/9001": linked,
        f"{repo}/issues/9001/comments": [],
        f"{repo}/issues/9001/timeline": [],
        f"{repo}/pulls/9001/reviews": [],
        f"{repo}/pulls/9001/comments": [],
        f"{repo}/commits/{'c' * 40}/check-runs": {"check_runs": []},
        f"{repo}/commits/{'c' * 40}/statuses": [],
    }
    (tmp_path / "routes.json").write_text(json.dumps(routes))
    (tmp_path / "fake_gh.py").write_text(FAKE_GH)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{tmp_path / "fake_gh.py"}" '
        f'"{tmp_path / "routes.json"}" "$@"\n'
    )
    gh.chmod(0o755)

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/collect_fastmcp_stack_evidence.sh"), "2026"],
        env={"PATH": f"{bin_dir}:/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin"},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    evidence = json.loads(result.stdout)
    assert [p["number"] for p in evidence["prs"]] == [9001]
