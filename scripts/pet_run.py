#!/usr/bin/env python3
"""Manage durable, resumable checkpoints for a Codex pet production run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


STAGES = (
    "intake",
    "preflight",
    "references",
    "base",
    "standard-rows",
    "cardinals",
    "look-row-9",
    "look-row-10",
    "assembly",
    "qa",
    "package",
    "installed",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def manifest_path(run_dir: Path) -> Path:
    return run_dir.expanduser().resolve() / "pet-factory.json"


def load(run_dir: Path) -> tuple[Path, dict]:
    path = manifest_path(run_dir)
    if not path.is_file():
        raise SystemExit(f"Run manifest not found: {path}")
    return path, json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, manifest: dict) -> None:
    manifest["updated_at"] = now()
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_artifact(run_dir: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (run_dir / path).resolve()


def command_init(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.expanduser().resolve()
    path = manifest_path(run_dir)
    if path.exists() and not args.force:
        raise SystemExit(f"Run already exists: {path}")
    for name in ("inputs", "generated", "decoded", "qa", "final", "logs"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    reference_manifest = args.reference_manifest.expanduser().resolve() if args.reference_manifest else None
    if reference_manifest and not reference_manifest.is_file():
        raise SystemExit(f"Reference manifest not found: {reference_manifest}")
    created = now()
    manifest = {
        "version": 1,
        "pet": {"id": args.pet_id, "display_name": args.display_name},
        "mode": args.mode,
        "contract": {"sprite_version_number": 2, "atlas": [1536, 2288], "grid": [8, 11], "cell": [192, 208]},
        "run_dir": str(run_dir),
        "reference_manifest": str(reference_manifest) if reference_manifest else None,
        "checkpoints": {stage: {"status": "pending", "artifacts": {}, "notes": []} for stage in STAGES},
        "provider_attempts": [],
        "created_at": created,
        "updated_at": created,
    }
    manifest["checkpoints"]["intake"]["status"] = "passed"
    manifest["checkpoints"]["intake"]["completed_at"] = created
    if reference_manifest:
        manifest["checkpoints"]["references"] = {
            "status": "passed",
            "completed_at": created,
            "artifacts": {"reference_manifest": str(reference_manifest)},
            "notes": [],
        }
    save(path, manifest)
    print(json.dumps({"ok": True, "manifest": str(path), "mode": args.mode}, ensure_ascii=False))
    return 0


def parse_artifacts(items: list[str]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Artifact must be KEY=PATH: {item}")
        key, value = item.split("=", 1)
        if not key or not value:
            raise SystemExit(f"Artifact must be KEY=PATH: {item}")
        artifacts[key] = value
    return artifacts


def command_checkpoint(args: argparse.Namespace) -> int:
    path, manifest = load(args.run_dir)
    run_dir = path.parent
    artifacts = parse_artifacts(args.artifact)
    resolved = {key: str(resolve_artifact(run_dir, value)) for key, value in artifacts.items()}
    if args.status == "passed":
        missing = [value for value in resolved.values() if not Path(value).exists()]
        if missing:
            raise SystemExit("Cannot pass checkpoint with missing artifact(s): " + ", ".join(missing))
    checkpoint = manifest["checkpoints"].setdefault(args.stage, {"artifacts": {}, "notes": []})
    checkpoint.setdefault("artifacts", {}).update(resolved)
    checkpoint.setdefault("notes", []).extend(args.note)
    checkpoint["status"] = args.status
    checkpoint["updated_at"] = now()
    if args.status == "passed":
        checkpoint["completed_at"] = now()
    save(path, manifest)
    print(json.dumps({"ok": True, "stage": args.stage, "status": args.status, "artifacts": resolved}, ensure_ascii=False))
    return 0


def command_provider(args: argparse.Namespace) -> int:
    path, manifest = load(args.run_dir)
    attempt = {
        "provider": args.provider,
        "model": args.model,
        "base_url": args.base_url,
        "input_bytes": args.input_bytes,
        "status": args.status,
        "output": str(args.output.expanduser().resolve()) if args.output else None,
        "note": args.note,
        "recorded_at": now(),
    }
    manifest.setdefault("provider_attempts", []).append(attempt)
    save(path, manifest)
    print(json.dumps({"ok": True, "provider_attempt": attempt}, ensure_ascii=False))
    return 0


def command_status(args: argparse.Namespace) -> int:
    path, manifest = load(args.run_dir)
    run_dir = path.parent
    stale: list[dict[str, str]] = []
    for stage, checkpoint in manifest.get("checkpoints", {}).items():
        if checkpoint.get("status") != "passed":
            continue
        for key, value in checkpoint.get("artifacts", {}).items():
            if not resolve_artifact(run_dir, value).exists():
                stale.append({"stage": stage, "artifact": key, "path": value})
    stale_stages = {item["stage"] for item in stale}
    effective_status = {
        stage: ("in_progress" if stage in stale_stages else manifest["checkpoints"].get(stage, {}).get("status", "pending"))
        for stage in STAGES
    }
    next_stage = next((stage for stage in STAGES if effective_status[stage] != "passed"), None)
    report = {
        "ok": not stale,
        "manifest": str(path),
        "pet": manifest.get("pet"),
        "mode": manifest.get("mode"),
        "next_stage": next_stage,
        "stale_artifacts": stale,
        "checkpoints": effective_status,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def command_discover(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    found = []
    for name in ("pet-factory.json", "pet_request.json", "hatch_pet_handoff.json"):
        for path in root.rglob(name):
            found.append({"type": name, "path": str(path), "modified": path.stat().st_mtime})
    found.sort(key=lambda item: item["modified"], reverse=True)
    print(json.dumps({"root": str(root), "count": len(found), "runs": found}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--run-dir", required=True, type=Path)
    init.add_argument("--pet-id", required=True)
    init.add_argument("--display-name", required=True)
    init.add_argument("--mode", choices=("fast", "strict"), default="fast")
    init.add_argument("--reference-manifest", type=Path)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=command_init)

    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--run-dir", required=True, type=Path)
    checkpoint.add_argument("--stage", required=True, choices=STAGES)
    checkpoint.add_argument("--status", required=True, choices=("pending", "in_progress", "passed", "failed"))
    checkpoint.add_argument("--artifact", action="append", default=[])
    checkpoint.add_argument("--note", action="append", default=[])
    checkpoint.set_defaults(func=command_checkpoint)

    provider = subparsers.add_parser("record-provider")
    provider.add_argument("--run-dir", required=True, type=Path)
    provider.add_argument("--provider", required=True)
    provider.add_argument("--model")
    provider.add_argument("--base-url")
    provider.add_argument("--input-bytes", type=int)
    provider.add_argument("--status", required=True, choices=("passed", "failed"))
    provider.add_argument("--output", type=Path)
    provider.add_argument("--note")
    provider.set_defaults(func=command_provider)

    status = subparsers.add_parser("status")
    status.add_argument("--run-dir", required=True, type=Path)
    status.set_defaults(func=command_status)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--root", required=True, type=Path)
    discover.set_defaults(func=command_discover)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
