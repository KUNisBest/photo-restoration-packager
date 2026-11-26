#!/usr/bin/env python3
"""Package an asset directory and verify the resulting ZIP."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from PIL import Image


def image_records(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.png")):
        with Image.open(path) as image:
            records.append(
                {"file": path.name, "width": image.width, "height": image.height}
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    zip_path = Path(args.zip).resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    source = image_records(root / "source")
    enhanced = image_records(root / "enhanced-4x")
    vector = image_records(root / "vector-renders")
    report = {
        "source_count": len(source),
        "ai_upscaled_count": len(enhanced),
        "vector_render_count": len(vector),
        "final_count": len(enhanced) + len(vector),
        "source_images": source,
        "ai_upscaled_images": enhanced,
        "vector_render_images": vector,
    }

    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.resolve() != zip_path
        and path.suffix.lower() not in {".zip", ".tmp"}
        and "__pycache__" not in path.parts
    ]
    report_path = root / "qa-report.json"
    report["archive_files"] = len(files) + 1
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    files.append(report_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(set(files)):
            package.write(path, arcname=path.relative_to(root))

    with zipfile.ZipFile(zip_path) as package:
        bad_member = package.testzip()
        if bad_member:
            raise RuntimeError(f"ZIP integrity check failed: {bad_member}")
        entries = len(package.namelist())

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    report["zip_path"] = str(zip_path)
    report["zip_size_bytes"] = zip_path.stat().st_size
    report["zip_entries"] = entries
    report["sha256"] = digest
    report["zip_testzip"] = "OK"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"zip={zip_path}")
    print(f"entries={entries}")
    print(f"bytes={zip_path.stat().st_size}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
