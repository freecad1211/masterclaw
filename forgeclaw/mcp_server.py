"""Built-in MCP server for ForgeClaw's read-only workspace and safe test tools.

Run with: python -m forgeclaw.mcp_server
The server uses the current working directory as its workspace root.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ForgeClaw Workspace")
ROOT = Path(os.getenv("FORGECLAW_MCP_WORKSPACE", os.getcwd())).resolve()
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".next", ".forgeclaw"}
SKIP_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}


def _safe_path(relative_path: str) -> Path:
    target = (ROOT / relative_path).resolve()
    if target != ROOT and ROOT not in target.parents:
        raise ValueError("Path escapes the configured workspace.")
    if any(part in SKIP_DIRS for part in target.relative_to(ROOT).parts):
        raise ValueError("Access to excluded directories is blocked.")
    if target.name in SKIP_NAMES or target.name.startswith(".env."):
        raise ValueError("Secret/config files are not readable through this tool.")
    return target


@mcp.tool()
def workspace_tree(max_entries: int = 200) -> list[str]:
    """List relative project files, excluding dependency caches and secrets."""
    entries: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_file() and path.name not in SKIP_NAMES and not path.name.startswith(".env."):
            entries.append(path.relative_to(ROOT).as_posix())
            if len(entries) >= min(max_entries, 500):
                break
    return sorted(entries)


@mcp.tool()
def read_file(path: str, max_chars: int = 12000) -> str:
    """Read a bounded UTF-8 text file inside the workspace; secret files are blocked."""
    target = _safe_path(path)
    if not target.is_file():
        raise ValueError("File not found.")
    return target.read_text(encoding="utf-8")[:max(1, min(max_chars, 20000))]


@mcp.tool()
def search_files(query: str, max_results: int = 30) -> list[dict[str, str]]:
    """Search text files in the workspace; return bounded path and matching line snippets."""
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    found: list[dict[str, str]] = []
    for rel in workspace_tree(500):
        path = _safe_path(rel)
        if path.suffix.lower() not in {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".ts", ".tsx", ".js", ".jsx", ".css", ".html"}:
            continue
        try:
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if query.casefold() in line.casefold():
                    found.append({"path": rel, "line": str(line_no), "text": line[:400]})
                    if len(found) >= min(max_results, 100):
                        return found
        except (OSError, UnicodeDecodeError):
            continue
    return found


@mcp.tool()
def workspace_status() -> dict[str, str]:
    """Return the configured workspace path and current Git branch."""
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    return {"workspace": str(ROOT), "branch": branch.stdout.strip(), "status": status.stdout[:4000]}


@mcp.tool()
def git_status() -> str:
    """Return bounded Git status output."""
    result = subprocess.run(["git", "status", "--short", "--branch"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError(result.stderr[:2000])
    return result.stdout[:6000]


@mcp.tool()
def git_diff() -> str:
    """Return a bounded diff of working-tree changes; does not expose untracked file contents."""
    result = subprocess.run(["git", "diff", "--no-ext-diff", "--"], cwd=ROOT, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr[:2000])
    return result.stdout[:16000]


@mcp.tool()
def run_tests(command: str = "pytest") -> dict[str, str | int]:
    """Run an allowlisted test command; arbitrary shell commands are rejected."""
    allowed = {
        "pytest": ["pytest"],
        "python -m pytest": ["python", "-m", "pytest"],
        "python -m compileall forgeclaw": ["python", "-m", "compileall", "forgeclaw"],
    }
    if command not in allowed:
        raise ValueError("Only pytest, python -m pytest, and python -m compileall forgeclaw are allowed.")
    result = subprocess.run(allowed[command], cwd=ROOT, capture_output=True, text=True, timeout=300)
    return {"exit_code": result.returncode, "output": (result.stdout + "\n" + result.stderr)[-10000:]}


if __name__ == "__main__":
    mcp.run()
