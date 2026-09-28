import copy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from src.core import workflow_contract


def _fixture_repo(tmp_path):
    (tmp_path / "workflow").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "AGENTS.md").write_text("agents\n")
    (tmp_path / "docs" / "PRODUCTION_WORKFLOW.md").write_text("workflow\n")
    (tmp_path / "docs" / "DIRECTOR_SPEC_WORKFLOW.md").write_text("director\n")
    (tmp_path / "workflow" / "CURRENT.json").write_text(json.dumps({
        "schema_version": 1,
        "workflow_id": "wf",
        "workflow_version": "1",
        "required_tool_profile": "core-production",
        "bridge_compatibility": {
            "minimum_version": "0.10.0",
            "required_tools": ["video_workflow_bootstrap"],
            "required_capabilities": ["bridge-compat-contract-v1"],
        },
        "core_docs": ["AGENTS.md", "docs/PRODUCTION_WORKFLOW.md"],
        "lane_docs": {"cinematic": ["docs/DIRECTOR_SPEC_WORKFLOW.md"], "animation": [], "business": []},
    }))
    return tmp_path


def _fake_git(repo, *args, timeout=15.0):
    if args[:2] == ("rev-parse", "HEAD"):
        return 0, "abc123", ""
    if args[:2] == ("branch", "--show-current"):
        return 0, "main", ""
    if args[:3] == ("rev-parse", "--abbrev-ref", "--symbolic-full-name"):
        return 0, "origin/main", ""
    if args and args[0] == "rev-list":
        return 0, "0\t0", ""
    if args[:2] == ("status", "--porcelain"):
        return 0, "", ""
    if args and args[0] == "fetch":
        return 0, "", ""
    return 0, "", ""




def _with_compatible_bridge(boot):
    result = copy.deepcopy(boot)
    result["bridge_compatibility"] = {
        "evaluated": True,
        "compatible": True,
        "minimum_version": "0.10.0",
        "actual_version": "0.10.0",
        "required_profile": "core-production",
        "active_profile": "core-production",
        "missing_tools": [],
        "missing_capabilities": [],
    }
    result["production_ready"] = True
    return result


def test_bootstrap_receipt_is_deterministic_and_lane_scoped(tmp_path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    monkeypatch.setattr(workflow_contract, "_git", _fake_git)
    a = workflow_contract.bootstrap(repo=repo, goal="highway film", refresh_remote=False, allow_unverified_remote=True)
    b = workflow_contract.bootstrap(repo=repo, lane="cinematic", refresh_remote=False, allow_unverified_remote=True)
    assert a["ready"] is True
    assert a["lane"] == "cinematic"
    assert a["receipt_sha256"] == b["receipt_sha256"]
    assert a["bridge_compatibility_requirements"]["minimum_version"] == "0.10.0"
    assert a["bridge_compatibility_requirements"]["required_capabilities"] == ["bridge-compat-contract-v1"]
    assert [x["path"] for x in a["required_docs"]] == [
        "AGENTS.md",
        "docs/PRODUCTION_WORKFLOW.md",
        "docs/DIRECTOR_SPEC_WORKFLOW.md",
    ]


def test_bound_production_detects_workflow_drift(tmp_path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    monkeypatch.setattr(workflow_contract, "_git", _fake_git)
    boot = workflow_contract.bootstrap(repo=repo, lane="cinematic", refresh_remote=False, allow_unverified_remote=True)
    compatible = _with_compatible_bridge(boot)
    data = {"lane": "animation", "workflow": {"bootstrap_required": True, "bootstrap": {}}}
    workflow_contract.bind_manifest(data, compatible, allow_unverified_remote=True)
    status = workflow_contract.binding_status(data, repo=repo, refresh_remote=False)
    assert status["ok"] is True

    (repo / "docs" / "DIRECTOR_SPEC_WORKFLOW.md").write_text("changed\n")
    stale = workflow_contract.binding_status(data, repo=repo, refresh_remote=False)
    assert stale["ok"] is False
    assert any("docs_sha256" in item for item in stale["errors"])

def test_native_bootstrap_cannot_bind_final_production_without_bridge_evidence(tmp_path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    monkeypatch.setattr(workflow_contract, "_git", _fake_git)
    boot = workflow_contract.bootstrap(repo=repo, lane="cinematic", refresh_remote=False, allow_unverified_remote=True)
    data = {"lane": "cinematic", "workflow": {"bootstrap_required": True, "bootstrap": {}}}
    try:
        workflow_contract.bind_manifest(data, boot, allow_unverified_remote=True)
    except ValueError as exc:
        assert "evaluated compatible bridge evidence" in str(exc)
    else:
        raise AssertionError("native unverified bootstrap unexpectedly bound production")


def test_render_dispatch_revalidates_running_bridge_profile(tmp_path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    monkeypatch.setattr(workflow_contract, "_git", _fake_git)
    native = workflow_contract.bootstrap(repo=repo, lane="cinematic", refresh_remote=False, allow_unverified_remote=True)
    compatible = _with_compatible_bridge(native)
    compatible["bridge_compatibility"]["tool_names_sha256"] = "tools-hash"
    compatible["bridge_compatibility"]["source_commit"] = "bridge-commit"
    data = {"lane": "cinematic", "workflow": {"bootstrap_required": True, "bootstrap": {}}}
    workflow_contract.bind_manifest(data, compatible, allow_unverified_remote=True)

    live = {
        "ok": True,
        "ready": True,
        "service": "hermes-mcp-bridge",
        "version": "0.10.0",
        "tool_profile": "core-production",
        "tool_names_sha256": "tools-hash",
        "source_commit": "bridge-commit",
        "capability_contract": {"capabilities": ["bridge-compat-contract-v1"]},
    }
    status = workflow_contract.binding_status(
        data, repo=repo, refresh_remote=False, live_bridge_status=live, require_active_bridge=True
    )
    assert status["ok"] is True

    changed = dict(live)
    changed["tool_profile"] = "core"
    stale = workflow_contract.binding_status(
        data, repo=repo, refresh_remote=False, live_bridge_status=changed, require_active_bridge=True
    )
    assert stale["ok"] is False
    assert any("tool profile changed" in error for error in stale["errors"])

    # Reusing an old compatible bootstrap object cannot mask current runtime drift.
    old_bootstrap = _with_compatible_bridge(native)
    still_stale = workflow_contract.binding_status(
        data,
        repo=repo,
        refresh_remote=False,
        active_bootstrap=old_bootstrap,
        live_bridge_status=changed,
        require_active_bridge=True,
    )
    assert still_stale["ok"] is False

def test_query_live_bridge_status_reads_running_endpoint(monkeypatch):
    payload = {
        "ok": True,
        "ready": True,
        "service": "hermes-mcp-bridge",
        "version": "0.10.0",
        "tool_profile": "core-production",
        "tool_names_sha256": "tools-hash",
        "source_commit": "bridge-commit",
        "capability_contract": {"capabilities": ["bridge-compat-contract-v1"]},
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv(
            "HERMES_MCP_READYZ_URL",
            f"http://127.0.0.1:{server.server_address[1]}/readyz",
        )
        live = workflow_contract.query_live_bridge_status()
        assert live["tool_profile"] == "core-production"
        requirements = {
            "minimum_version": "0.10.0",
            "required_capabilities": ["bridge-compat-contract-v1"],
        }
        bound = {
            "required_profile": "core-production",
            "actual_version": "0.10.0",
            "tool_names_sha256": "tools-hash",
            "source_commit": "bridge-commit",
        }
        assert workflow_contract.validate_live_bridge_status(
            live, requirements=requirements, bound_compat=bound
        ) == []

        payload["tool_profile"] = "core"
        changed = workflow_contract.query_live_bridge_status()
        errors = workflow_contract.validate_live_bridge_status(
            changed, requirements=requirements, bound_compat=bound
        )
        assert any("tool profile changed" in error for error in errors)
    finally:
        server.shutdown()
        server.server_close()


def test_bootstrap_surfaces_lane_brief(tmp_path, monkeypatch):
    repo = _fixture_repo(tmp_path)
    current_path = repo / "workflow" / "CURRENT.json"
    current = json.loads(current_path.read_text())
    current["lane_briefs"] = {"cinematic": "workflow/cinematic-brief.md"}
    current_path.write_text(json.dumps(current))
    (repo / "workflow" / "cinematic-brief.md").write_text("brief\n")
    monkeypatch.setattr(workflow_contract, "_git", _fake_git)
    boot = workflow_contract.bootstrap(
        repo=repo, lane="cinematic", refresh_remote=False, allow_unverified_remote=True
    )
    assert boot["lane_brief"]["path"] == "workflow/cinematic-brief.md"
    assert boot["lane_brief"]["exists"] is True
