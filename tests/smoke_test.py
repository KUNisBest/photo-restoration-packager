#!/usr/bin/env python3

import py_compile
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def test_skill_frontmatter(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter, body = text[4:].split("\n---\n", 1)
        self.assertIn("name: photo-restoration-packager", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("照片变清晰", frontmatter)
        self.assertIn("Fidelity and safety rules", body)
        self.assertTrue((ROOT / "README.md").exists())
        self.assertTrue((ROOT / "README.en.md").exists())
        self.assertIn(
            "MIT License",
            (ROOT / "LICENSE").read_text(encoding="utf-8"),
        )

    def test_scripts_compile(self):
        with tempfile.TemporaryDirectory() as temp_name:
            for script in (ROOT / "scripts").glob("*.py"):
                py_compile.compile(
                    script,
                    cfile=str(Path(temp_name) / f"{script.stem}.pyc"),
                    doraise=True,
                )

    def test_package_results(self):
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            root = temp / "assets"
            for directory in ("source", "enhanced-4x", "vector-renders"):
                (root / directory).mkdir(parents=True)
                Image.new("RGB", (32, 32), "white").save(root / directory / "image.png")
            (root / "README.md").write_text("test", encoding="utf-8")

            archive = temp / "result.zip"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "package_results.py"),
                    "--root",
                    str(root),
                    "--zip",
                    str(archive),
                ],
                check=True,
            )
            with zipfile.ZipFile(archive) as package:
                self.assertIsNone(package.testzip())
                names = set(package.namelist())
            self.assertIn("source/image.png", names)
            self.assertIn("enhanced-4x/image.png", names)
            self.assertIn("vector-renders/image.png", names)
            self.assertIn("qa-report.json", names)


if __name__ == "__main__":
    unittest.main()
