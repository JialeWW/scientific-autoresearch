from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build_installable_skill.py"
SKILL_DIR = ROOT / "scientific-autoresearch"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_installable_skill", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installable-skill builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LightweightInstallSurfaceTests(unittest.TestCase):
    def test_stochastic_policy_is_design_appropriate(self) -> None:
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("master random seed `42`", content)
        self.assertIn("reproducible randomization policy appropriate to the design", content)
        self.assertIn("never select or change randomness after outcomes", content)
        self.assertIn("separate validated concealed scheme", content)

    def test_runtime_file_list_excludes_formal_audit(self) -> None:
        builder = load_builder()
        relative = {
            path.relative_to(SKILL_DIR).as_posix()
            for path in builder.runtime_files(SKILL_DIR)
        }
        self.assertIn("SKILL.md", relative)
        self.assertTrue(any(path.startswith("references/") for path in relative))
        self.assertFalse(any(path.startswith("scripts/") for path in relative))
        self.assertFalse(relative & builder.FORBIDDEN_RUNTIME_MEMBERS)

    def test_archive_is_deterministic_and_lightweight(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.zip"
            second = root / "second.zip"
            first_receipt = builder.build(SKILL_DIR, first)
            second_receipt = builder.build(SKILL_DIR, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(
                first_receipt["runtime_package_sha256"],
                second_receipt["runtime_package_sha256"],
            )
            self.assertFalse(first_receipt["historical_evals_included"])
            self.assertFalse(first_receipt["formal_machine_audit_included"])

            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())
            self.assertIn("scientific-autoresearch/SKILL.md", names)
            self.assertIn("scientific-autoresearch/LICENSE", names)
            self.assertFalse(any("/evals/" in name for name in names))
            self.assertFalse(any("/scripts/" in name for name in names))
            self.assertFalse(
                {
                    f"scientific-autoresearch/{path}"
                    for path in builder.FORBIDDEN_RUNTIME_MEMBERS
                }
                & names
            )


if __name__ == "__main__":
    unittest.main()
