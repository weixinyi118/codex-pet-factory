#!/usr/bin/env python3
"""Read-only preflight for Codex v2 pet production."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


REQUIRED_HATCH_SCRIPTS = (
    "extract_strip_frames.py",
    "assemble_extended_atlas.py",
    "despill_chroma_edges.py",
    "make_contact_sheet.py",
    "make_direction_qa_sheet.py",
    "measure_direction_continuity.py",
    "render_animation_previews.py",
    "validate_atlas.py",
)


def safe_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if not parts.scheme or not parts.netloc:
            return value
        host = parts.hostname or ""
        port = f":{parts.port}" if parts.port else ""
        return urlunsplit((parts.scheme, host + port, parts.path.rstrip("/"), "", ""))
    except Exception:
        return "<configured>"


def collect_base_urls(value: object, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower().replace("-", "_") in {"base_url", "api_base", "endpoint"} and isinstance(child, str):
                found.add(safe_url(child))
            else:
                collect_base_urls(child, found)
    elif isinstance(value, list):
        for child in value:
            collect_base_urls(child, found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    codex_home = (args.codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))).expanduser().resolve()
    hatch_dir = codex_home / "skills" / "hatch-pet"
    pets_dir = codex_home / "pets"
    config_path = codex_home / "config.toml"

    errors: list[str] = []
    warnings: list[str] = []
    base_urls: set[str] = set()

    try:
        from PIL import Image  # noqa: F401

        pillow_ok = True
    except Exception:
        pillow_ok = False
        errors.append("Pillow is not installed in this Python runtime")

    missing_scripts = [name for name in REQUIRED_HATCH_SCRIPTS if not (hatch_dir / "scripts" / name).is_file()]
    if not hatch_dir.is_dir():
        errors.append(f"hatch-pet skill not found: {hatch_dir}")
    elif missing_scripts:
        errors.append("hatch-pet is missing required scripts: " + ", ".join(missing_scripts))

    if not pets_dir.exists():
        warnings.append(f"pets directory does not exist yet: {pets_dir}")

    config_readable = False
    if config_path.is_file():
        try:
            import tomllib

            with config_path.open("rb") as handle:
                config = tomllib.load(handle)
            collect_base_urls(config, base_urls)
            config_readable = True
        except Exception as exc:
            warnings.append(f"Could not parse config.toml: {type(exc).__name__}")
    else:
        warnings.append(f"Codex config not found: {config_path}")

    key_names = ("OPENAI_API_KEY", "DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ALIBABA_CLOUD_API_KEY")
    key_presence = {name: bool(os.environ.get(name)) for name in key_names}

    report = {
        "ok": not errors,
        "python": {"executable": sys.executable, "version": sys.version.split()[0], "pillow": pillow_ok},
        "codex_home": str(codex_home),
        "pets_dir": str(pets_dir),
        "hatch_pet_dir": str(hatch_dir),
        "hatch_pet_missing_scripts": missing_scripts,
        "config": {"path": str(config_path), "readable": config_readable, "base_urls": sorted(base_urls)},
        "provider_key_present": key_presence,
        "errors": errors,
        "warnings": warnings,
        "note": "Key values were not read or printed. No network request was made.",
    }

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
