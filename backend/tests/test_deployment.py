import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATABASE_PACKAGES = {"psycopg2-binary", "sqlalchemy"}


def _package_name(requirement: str) -> str:
    return re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip()


def test_vercel_manifests_include_database_dependencies():
    requirements = {
        _package_name(line)
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    }
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_dependencies = {
        _package_name(requirement) for requirement in pyproject["project"]["dependencies"]
    }

    assert DATABASE_PACKAGES <= requirements
    assert DATABASE_PACKAGES <= project_dependencies
