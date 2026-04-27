from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


def run(cmd: list[str], timeout: int = 15) -> CommandResult:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            ok=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            returncode=proc.returncode,
        )
    except Exception as exc:
        return CommandResult(ok=False, stdout="", stderr=str(exc), returncode=999)


def run_powershell(command: str, timeout: int = 20) -> CommandResult:
    return run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command,
    ], timeout=timeout)
