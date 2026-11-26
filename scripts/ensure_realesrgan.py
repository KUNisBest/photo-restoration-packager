#!/usr/bin/env python3
"""Download and unpack the official portable Real-ESRGAN NCNN release."""

import argparse
import concurrent.futures
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


RELEASES = {
    "win32": (
        "realesrgan-ncnn-vulkan-20220424-windows.zip",
        "realesrgan-ncnn-vulkan.exe",
    ),
    "darwin": (
        "realesrgan-ncnn-vulkan-20220424-macos.zip",
        "realesrgan-ncnn-vulkan",
    ),
    "linux": (
        "realesrgan-ncnn-vulkan-20220424-ubuntu.zip",
        "realesrgan-ncnn-vulkan",
    ),
}
BASE_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/"
)


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def _download_part(
    url: str,
    start: int,
    end: int,
    destination: Path,
) -> None:
    expected = end - start + 1
    existing = destination.stat().st_size if destination.exists() else 0
    if existing > expected:
        destination.unlink()
        existing = 0

    while existing < expected:
        segment_start = start + existing
        segment_end = min(end, segment_start + 64 * 1024 - 1)
        segment_size = segment_end - segment_start + 1
        payload = None
        for attempt in range(1, 7):
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Codex",
                    "Range": f"bytes={segment_start}-{segment_end}",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    candidate = response.read()
                if len(candidate) != segment_size:
                    raise RuntimeError(
                        f"Segment returned {len(candidate)} bytes, "
                        f"expected {segment_size}"
                    )
                payload = candidate
                break
            except Exception:
                if attempt == 6:
                    raise
                time.sleep(attempt)
        with destination.open("ab" if existing else "wb") as stream:
            stream.write(payload)
            stream.flush()
        existing += len(payload)


def _download_archive(url: str, destination: Path, parts: int = 128) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Codex", "Range": "bytes=0-0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        total_size = int(response.headers["Content-Range"].rsplit("/", 1)[1])

    chunk_size = (total_size + parts - 1) // parts
    jobs = []
    for index in range(parts):
        start = index * chunk_size
        end = min(total_size - 1, start + chunk_size - 1)
        if start > end:
            break
        part_path = destination.with_suffix(destination.suffix + f".part{index:03d}")
        jobs.append((start, end, part_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        futures = [
            executor.submit(_download_part, url, start, end, part_path)
            for start, end, part_path in jobs
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    with destination.open("wb") as stream:
        for _, _, part_path in jobs:
            stream.write(part_path.read_bytes())
            part_path.unlink()
    if destination.stat().st_size != total_size:
        raise RuntimeError("Downloaded archive size does not match Content-Range")


def ensure_realesrgan(tool_dir: Path, parts: int = 128) -> Path:
    platform_key = _platform_key()
    archive_name, executable_name = RELEASES[platform_key]
    executable = tool_dir / executable_name
    if executable.exists():
        return executable

    tool_dir.mkdir(parents=True, exist_ok=True)
    archive = tool_dir.with_suffix(".zip")
    if not archive.exists():
        _download_archive(BASE_URL + archive_name, archive, parts=parts)

    with zipfile.ZipFile(archive) as package:
        bad_member = package.testzip()
        if bad_member:
            raise RuntimeError(f"Corrupt Real-ESRGAN archive member: {bad_member}")
        package.extractall(tool_dir)
    if not executable.exists():
        raise FileNotFoundError(f"Real-ESRGAN executable not found: {executable}")
    if platform_key != "win32":
        executable.chmod(executable.stat().st_mode | 0o111)
    return executable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool-dir", required=True)
    parser.add_argument("--parts", type=int, default=128)
    args = parser.parse_args()
    executable = ensure_realesrgan(Path(args.tool_dir), parts=args.parts)
    print(executable)


if __name__ == "__main__":
    main()
