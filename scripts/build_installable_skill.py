#!/usr/bin/env python3
"""Build the deterministic runtime-only scientific-autoresearch skill archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ARCHIVE_FORMAT = "scientific-autoresearch-installable-skill-v1"
DIGEST_PROFILE = b"scientific-autoresearch-runtime-package-v2\0"
ARCHIVE_ROOT = "scientific-autoresearch"


def runtime_files(source: Path) -> list[Path]:
    source = source.resolve()
    skill_md = source / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        raise ValueError("SKILL.md must be a regular, nonsymlink file")

    files = [skill_md]
    for directory_name, pattern in (("references", "*.md"), ("scripts", "*.py")):
        directory = source / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"{directory_name} must be a regular, nonsymlink directory")
        matches = sorted(directory.glob(pattern), key=lambda path: path.name)
        if not matches:
            raise ValueError(f"{directory_name}/{pattern} matched no files")
        if any(path.is_symlink() or not path.is_file() for path in matches):
            raise ValueError(f"{directory_name} contains an invalid runtime file")
        files.extend(matches)
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
    return {
        "archive_format": ARCHIVE_FORMAT,
        "artifact_path": str(output),
        "artifact_sha256": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest(),
        "runtime_package_sha256": runtime_digest(source, files),
        "file_count": len(members),
        "historical_evals_included": False,
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
