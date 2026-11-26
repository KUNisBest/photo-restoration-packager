#!/usr/bin/env python3
"""Batch wrapper around the portable Real-ESRGAN NCNN executable."""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from ensure_realesrgan import ensure_realesrgan


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def collect_inputs(source: Path, max_source_side: int) -> list[Path]:
    if source.is_file():
        return [source]
    images = [
        path
        for path in sorted(source.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if max_source_side <= 0:
        return images
    from PIL import Image

    accepted = []
    for path in images:
        with Image.open(path) as image:
            if max(image.size) <= max_source_side:
                accepted.append(path)
    return accepted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--tool-dir")
    parser.add_argument("--scale", type=int, choices=(2, 3, 4), default=4)
    parser.add_argument("--tile", type=int, default=512)
    parser.add_argument("--gpu", type=int)
    parser.add_argument(
        "--max-source-side",
        type=int,
        default=0,
        help="Skip inputs larger than this; 0 processes every input.",
    )
    parser.add_argument("--download-parts", type=int, default=128)
    args = parser.parse_args()

    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    tool_dir = (
        Path(args.tool_dir).resolve()
        if args.tool_dir
        else Path(tempfile.gettempdir()) / "codex-realesrgan"
    )
    executable = ensure_realesrgan(tool_dir, parts=args.download_parts)

    inputs = collect_inputs(source, args.max_source_side)
    if not inputs:
        raise RuntimeError("No eligible input images found")

    with tempfile.TemporaryDirectory(prefix="real-esrgan-input-") as temp_name:
        staging = Path(temp_name)
        for path in inputs:
            shutil.copy2(path, staging / path.name)

        command = [
            str(executable),
            "-i",
            str(staging),
            "-o",
            str(output),
            "-n",
            "realesrgan-x4plus",
            "-s",
            str(args.scale),
            "-t",
            str(args.tile),
        ]
        if args.gpu is not None:
            command.extend(["-g", str(args.gpu)])
        subprocess.run(command, check=True, cwd=tool_dir)

    results = [
        path
        for path in output.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    ]
    if not results:
        raise RuntimeError("Real-ESRGAN produced no output images")
    print(f"processed={len(inputs)}")
    print(f"outputs={len(results)}")
    print(f"directory={output}")


if __name__ == "__main__":
    main()
