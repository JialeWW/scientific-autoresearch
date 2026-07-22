#!/usr/bin/env python3
"""Build a deterministic behavior-package ZIP for benchmark verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


DIGEST_PROFILE = "scientific-autoresearch-behavior-package-v1"
ARTIFACT_FORMAT = "scientific-autoresearch-behavior-package-zip-v1"


def behavior_files(root: Path) -> list[Path]:
    root = root.resolve()
    skill_md = root / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        raise ValueError("SKILL.md must be a regular, nonsymlink file")
    files = [skill_md]
    for directory_name, pattern in (
        ("references", "*.md"),
        ("scripts", "*.py"),
        ("evals", "*.json"),
    ):
        directory = root / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"{directory_name} must be a regular directory")
        matches = sorted(directory.glob(pattern), key=lambda path: path.name)
        if not matches:
            raise ValueError(f"{directory_name}/{pattern} matched no files")
        if any(path.is_symlink() or not path.is_file() for path in matches):
            raise ValueError(f"{directory_name} contains an invalid behavior file")
        files.extend(matches)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def package_digest(members: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(DIGEST_PROFILE.encode("utf-8") + b"\0")
    for relative, payload in sorted(members.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
    return "sha256:" + digest.hexdigest()


def build(source: Path, output: Path) -> dict[str, object]:
    source = source.resolve()
    files = behavior_files(source)
    members = {
        path.relative_to(source).as_posix(): path.read_bytes() for path in files
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for relative, payload in sorted(members.items()):
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, payload)
    return {
        "artifact_format": ARTIFACT_FORMAT,
        "artifact_path": str(output),
        "artifact_sha256": "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest(),
        "behavior_package_sha256": package_digest(members),
        "file_count": len(members),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.source, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
