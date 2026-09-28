import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-workflow-version-bump.py"
spec = importlib.util.spec_from_file_location("workflow_version_bump", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def _contract(version="1"):
    return {
        "workflow_version": version,
        "core_docs": ["AGENTS.md", "docs/PRODUCTION_WORKFLOW.md"],
        "lane_docs": {"cinematic": ["docs/QUALITY_FLOOR.md"]},
        "lane_briefs": {"cinematic": "workflow/cinematic-brief.md"},
    }


def test_canonical_doc_change_requires_version_bump():
    required, relevant = module.requires_version_bump({"AGENTS.md"}, _contract("1"), _contract("1"))
    assert required is True
    assert relevant == ["AGENTS.md"]


def test_version_bump_satisfies_contract_change():
    required, relevant = module.requires_version_bump({"docs/QUALITY_FLOOR.md"}, _contract("1"), _contract("2"))
    assert required is False
    assert relevant == ["docs/QUALITY_FLOOR.md"]


def test_noncanonical_readme_change_does_not_require_workflow_bump():
    required, relevant = module.requires_version_bump({"README.md"}, _contract("1"), _contract("1"))
    assert required is False
    assert relevant == []
