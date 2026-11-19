"""Shared test setup."""

import pytest


@pytest.fixture(autouse=True)
def git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Commits made by the code under test need an identity; CI runners have none configured."""
    for kind in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{kind}_NAME", "test")
        monkeypatch.setenv(f"GIT_{kind}_EMAIL", "test@example.invalid")
