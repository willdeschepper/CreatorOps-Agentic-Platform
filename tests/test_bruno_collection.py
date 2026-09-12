import re
from pathlib import Path

from creatorops.main import app

BRUNO_ROOT = Path(__file__).parents[1] / "bruno"
HTTP_METHOD = re.compile(r"^(get|post|put|patch|delete|options|head) \{", re.MULTILINE)
REQUEST_URL = re.compile(r"^\s+url: (.+)$", re.MULTILINE)
PATH_PARAMETER = re.compile(r"\{\{[^{}]+\}\}|\{[^{}]+\}")


def _normalized_path(url: str) -> str:
    path = re.sub(r"^\{\{(?:base_url|provider_url)\}\}", "", url)
    path = path.split("?", maxsplit=1)[0]
    return PATH_PARAMETER.sub("{parameter}", path)


def _bruno_operations() -> tuple[set[tuple[str, str]], list[Path]]:
    operations: set[tuple[str, str]] = set()
    requests: list[Path] = []
    for path in BRUNO_ROOT.rglob("*.bru"):
        content = path.read_text()
        method = HTTP_METHOD.search(content)
        url = REQUEST_URL.search(content)
        if method is None and url is None:
            continue
        assert method is not None and url is not None, f"Malformed Bruno request: {path}"
        assert "tests {" in content, f"Bruno request has no contract tests: {path}"
        operations.add((method.group(1).upper(), _normalized_path(url.group(1))))
        requests.append(path)
    return operations, requests


def test_bruno_covers_every_public_creatorops_operation() -> None:
    actual, requests = _bruno_operations()
    expected = {
        (method.upper(), PATH_PARAMETER.sub("{parameter}", path))
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }

    assert expected <= actual, f"Missing Bruno operations: {sorted(expected - actual)}"
    assert len(requests) >= 45


def test_bruno_environment_contains_the_complete_business_chain() -> None:
    environment = (BRUNO_ROOT / "environments" / "local.bru").read_text()
    for variable in (
        "owner_token",
        "creator_a_token",
        "program_id",
        "membership_a_id",
        "coupon_a_code",
        "click_id",
        "payout_id",
        "finding_id",
        "proposal_id",
    ):
        assert f"  {variable}:" in environment
