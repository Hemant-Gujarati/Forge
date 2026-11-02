import subprocess
from pathlib import Path

from forge.safety import WorkspaceGuard
from forge.tools.git import GitTools


def test_log_count_is_bounded(tmp_path: Path) -> None:
    tools = GitTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    assert tools.max_output_chars == 20_000


def test_commit_excludes_common_local_secrets(tmp_path: Path) -> None:
    repository_ignore = Path(__file__).resolve().parents[1] / ".gitignore"
    (tmp_path / ".gitignore").write_text(
        repository_ignore.read_text(encoding="utf-8"), encoding="utf-8"
    )
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Forge Tests"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "forge-tests@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "README.md").write_text("initial", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "initial"], cwd=tmp_path, check=True
    )

    (tmp_path / "README.md").write_text("safe update", encoding="utf-8")
    (tmp_path / ".env.production").write_text("token=secret", encoding="utf-8")
    (tmp_path / ".aws").mkdir()
    (tmp_path / ".aws" / "credentials").write_text(
        "access_key=secret", encoding="utf-8"
    )
    (tmp_path / "private.key").write_text("private key", encoding="utf-8")

    tools = GitTools(WorkspaceGuard([str(tmp_path)], tmp_path))
    tools.commit("safe update")
    committed_files = subprocess.run(
        ["git", "show", "--format=", "--name-only", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    assert "README.md" in committed_files
    assert ".env.production" not in committed_files
    assert ".aws/credentials" not in committed_files
    assert "private.key" not in committed_files
