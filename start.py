from __future__ import annotations

import os
import secrets
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
ENV_FILE = ROOT / ".env"
URL = "http://127.0.0.1:8000/ui"
MIN_PYTHON = (3, 11)


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        raise RuntimeError(
            f"Python 3.11 or newer is required. Current version: {sys.version.split()[0]}"
        )


def prepare_env() -> None:
    example = ROOT / ".env.example"
    if not ENV_FILE.exists():
        if not example.exists():
            raise FileNotFoundError(".env.example is missing.")
        shutil.copyfile(example, ENV_FILE)
        print("Created .env from .env.example.")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    token_found = False
    updated: list[str] = []
    for line in lines:
        if line.startswith("FORGECLAW_API_TOKEN="):
            token_found = True
            if not line.partition("=")[2].strip():
                line = "FORGECLAW_API_TOKEN=" + secrets.token_urlsafe(32)
                print("Generated a local FORGECLAW_API_TOKEN.")
        updated.append(line)
    if not token_found:
        updated.append("FORGECLAW_API_TOKEN=" + secrets.token_urlsafe(32))
        print("Added a local FORGECLAW_API_TOKEN.")
    ENV_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")


def install_dependencies(python: Path) -> None:
    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", "pip"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [str(python), "-m", "pip", "install", "-e", ".[dev]"],
        cwd=ROOT,
        check=True,
    )


def wait_for_server(process: subprocess.Popen[bytes], timeout: float = 25.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen("http://127.0.0.1:8000/health", timeout=0.5) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            time.sleep(0.25)
    return False


def main() -> int:
    ensure_python_version()
    prepare_env()

    if not VENV.exists():
        print("Creating the Python virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], cwd=ROOT, check=True)

    python = venv_python()
    if not python.exists():
        raise FileNotFoundError(f"Virtual environment Python was not found: {python}")

    print("Checking/installing ForgeClaw dependencies (first launch may take a few minutes)...")
    install_dependencies(python)

    command = [
        str(python), "-m", "uvicorn", "forgeclaw.main:app",
        "--host", "127.0.0.1", "--port", "8000",
    ]
    print("\nStarting ForgeClaw without Docker.")
    print(f"Control Room: {URL}")
    print("Keep this terminal open while using ForgeClaw. Press Ctrl+C to stop.\n")

    process = subprocess.Popen(command, cwd=ROOT)
    try:
        if wait_for_server(process):
            webbrowser.open(URL)
        return process.wait()
    except KeyboardInterrupt:
        print("\nStopping ForgeClaw...")
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"\nForgeClaw could not start: {exc}", file=sys.stderr)
        print("Check Python 3.11+, internet access for the first dependency install, and .env.", file=sys.stderr)
        raise SystemExit(1)
