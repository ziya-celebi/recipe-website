import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_PACKAGES = {"psycopg2-binary", "sqlalchemy"}


def _package_name(requirement: str) -> str:
    return re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip()


def _pyproject_dependencies() -> set[str]:
    dependencies = set()
    in_dependencies = False

    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.strip() == "dependencies = [":
            in_dependencies = True
            continue
        if in_dependencies and line.strip() == "]":
            break
        if in_dependencies:
            match = re.match(r'\s*"([^"]+)"', line)
            if match:
                dependencies.add(_package_name(match.group(1)))

    return dependencies


def test_vercel_manifests_include_database_dependencies():
    requirements = {
        _package_name(line)
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }

    assert DATABASE_PACKAGES <= requirements
    assert DATABASE_PACKAGES <= _pyproject_dependencies()
