"""Run required checks and retain actual output. Install browser first on Linux."""
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    npm = "npm.cmd" if os.name == "nt" else "npm"
    commands = [
        (ROOT, [sys.executable, "-m", "pytest", "backend/tests", "-q", "--junitxml=evidence/backend-tests.xml"]),
        (ROOT / "frontend", [npm, "run", "typecheck"]),
        (ROOT / "frontend", [npm, "run", "build"]),
        (ROOT, [sys.executable, "scripts/benchmark.py"]),
        (ROOT / "frontend", [npm, "run", "test:e2e"]),
    ]
    results = []
    for cwd, command in commands:
        print(f"Running: {' '.join(command)}", flush=True)
        try:
            completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       encoding="utf-8", errors="replace")
        except OSError as exc:
            completed = subprocess.CompletedProcess(command, 127, stdout=str(exc))
        print(completed.stdout, flush=True)
        results.append({"cwd": str(cwd.relative_to(ROOT)), "command": command,
                        "returncode": completed.returncode, "output": completed.stdout})
    (ROOT / "evidence/verification.json").write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
        "playwright_channel": os.environ.get("PLAYWRIGHT_CHANNEL", "bundled Chromium"), "checks": results,
    }, indent=2) + "\n")
    if any(result["returncode"] for result in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
