#!/usr/bin/env python3
"""Build the deterministic runtime-only scientific-autoresearch skill archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ARCHIVE_FORMAT = "scientific-autoresearch-installable-skill-v2"
DIGEST_PROFILE = b"scientific-autoresearch-runtime-package-v3\0"
ARCHIVE_ROOT = "scientific-autoresearch"
FORBIDDEN_RUNTIME_MEMBERS = {
    "references/report-contract.md",
    "references/status-schema.md",
    "references/round-gate-checklist.md",
    "scripts/validate_run.py",
}


def runtime_files(source: Path) -> list[Path]:
    source = source.resolve()
    skill_md = source / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        raise ValueError("SKILL.md must be a regular, nonsymlink file")

    files = [skill_md]
    references = source / "references"
    if references.is_symlink() or not references.is_dir():
        raise ValueError("references must be a regular, nonsymlink directory")
    matches = sorted(references.glob("*.md"), key=lambda path: path.name)
    if not matches:
        raise ValueError("references/*.md matched no files")
    if any(path.is_symlink() or not path.is_file() for path in matches):
        raise ValueError("references contains an invalid runtime file")
    files.extend(matches)

    relative_files = {path.relative_to(source).as_posix() for path in files}
    forbidden = sorted(relative_files & FORBIDDEN_RUNTIME_MEMBERS)
    if forbidden:
        raise ValueError(f"formal machine-audit files entered the runtime surface: {forbidden}")
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def runtime_digest(source: Path, files: list[Path]) -> str:
    source = source.resolve()
    digest = hashlib.sha256()
    digest.update(DIGEST_PROFILE)
    for path in files:
        relative = path.relative_to(source).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return "sha256:" + digest.hexdigest()


def build(source: Path, output: Path) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")

    files = runtime_files(source)
    members = {
        f"{ARCHIVE_ROOT}/{path.relative_to(source).as_posix()}": path.read_bytes()
        for path in files
    }
    license_path = source.parent / "LICENSE"
    if license_path.is_symlink() or not license_path.is_file():
        raise ValueError("repository LICENSE must be a regular, nonsymlink file")
    members[f"{ARCHIVE_ROOT}/LICENSE"] = license_path.read_bytes()

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for relative, payload in sorted(members.items()):
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, payload)

    names = sorted(members)
    if any("/evals/" in name or name.endswith("/evals") for name in names):
        raise AssertionError("historical evals entered the installable archive")
    if any("/scripts/" in name for name in names):
        raise AssertionError("runtime scripts entered the lightweight installable archive")
    if any(
        name.removeprefix(f"{ARCHIVE_ROOT}/") in FORBIDDEN_RUNTIME_MEMBERS
        for name in names
    ):
        raise AssertionError("formal machine-audit files entered the installable archive")
    return {
        "archive_format": ARCHIVE_FORMAT,
        "artifact_path": str(output),
        "artifact_sha256": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest(),
        "runtime_package_sha256": runtime_digest(source, files),
        "file_count": len(members),
        "historical_evals_included": False,
        "formal_machine_audit_included": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
