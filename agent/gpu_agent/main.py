from __future__ import annotations

import argparse
import platform
import sys

from .collector import collect_validation_checks
from .config import load_config
from .reporter import (
    build_event,
    build_validation_event,
    post_event,
    print_summary,
    write_event,
    write_heartbeat,
)
from .runners import run, run_powershell
from .utils import ensure_dir, hostname, os_type
from .version import __version__


def install(config) -> int:
    event = build_event(
        host=hostname(),
        env_type=config.env_type,
        os_type=os_type(),
        agent_version=__version__,
        config_version=config.config_version,
        event_type="install_started",
        severity="info",
        error_code="INSTALL_STARTED",
        message="install is wrapper-driven; verify platform install scripts executed",
        recommended_action="run gpu-agent validate",
    )
    write_event(config, event)
    print_summary(event)
    return 0


def validate(config) -> int:
    checks = collect_validation_checks(config, __version__)
    event, rc = build_validation_event(
        host=hostname(),
        env_type=config.env_type,
        os_type=os_type(),
        agent_version=__version__,
        config_version=config.config_version,
        checks=checks,
    )
    write_event(config, event)
    write_heartbeat(config, hostname(), config.env_type, os_type(), __version__, config.config_version)
    try:
        post_event(config, event)
    except Exception:
        pass
    print_summary(event)
    return rc


def repair(config) -> int:
    messages: list[str] = []
    if platform.system().lower().startswith("win"):
        res = run_powershell("Restart-Service -Name telegraf -Force")
        messages.append(res.stdout or res.stderr or "telegraf restart attempted")
    else:
        for svc in [config.telegraf_service_linux, config.dcgm_service_linux]:
            res = run(["systemctl", "restart", svc])
            messages.append(res.stdout or res.stderr or f"{svc} restart attempted")

    event = build_event(
        host=hostname(),
        env_type=config.env_type,
        os_type=os_type(),
        agent_version=__version__,
        config_version=config.config_version,
        event_type="repair_attempted",
        severity="warning",
        error_code="REPAIR_ATTEMPTED",
        message=" | ".join(messages),
        recommended_action="run gpu-agent validate",
    )
    write_event(config, event)
    try:
        post_event(config, event)
    except Exception:
        pass
    print_summary(event)
    return 0


def upgrade(config) -> int:
    event = build_event(
        host=hostname(),
        env_type=config.env_type,
        os_type=os_type(),
        agent_version=__version__,
        config_version=config.config_version,
        event_type="upgrade_required",
        severity="warning",
        error_code="UPGRADE_REQUIRED",
        message="download approved package from internal repository and rerun validation",
        recommended_action="execute platform-specific upgrade script, then run gpu-agent validate",
    )
    write_event(config, event)
    print_summary(event)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="gpu-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install")
    sub.add_parser("validate")
    sub.add_parser("repair")
    sub.add_parser("upgrade")
    sub.add_parser("version")

    args = parser.parse_args()
    config = load_config()
    if config.result_dir_notice:
        print(f"[GPU Agent] NOTICE - {config.result_dir_notice}", file=sys.stderr)
    ensure_dir(config.result_dir)

    if args.command == "version":
        print(__version__)
        raise SystemExit(0)
    if args.command == "install":
        raise SystemExit(install(config))
    if args.command == "validate":
        raise SystemExit(validate(config))
    if args.command == "repair":
        raise SystemExit(repair(config))
    if args.command == "upgrade":
        raise SystemExit(upgrade(config))

    raise SystemExit(1)


if __name__ == "__main__":
    main()
