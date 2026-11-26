#!/usr/bin/env python3
"""Audit a PDF page and extract an explicit allowlist of image assets."""

import argparse
import json
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader


def overlap_area(a: dict, b: tuple[float, float, float, float]) -> float:
    x0 = max(a["x0"], b[0])
    y0 = max(a["top"], b[1])
    x1 = min(a["x1"], b[2])
    y1 = min(a["bottom"], b[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def build_audit(pdf_path: Path, page_index: int) -> list[dict]:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_index]
        words = page.extract_words()
        records = []
        for image in page.images:
            area = max(
                0.001,
                (image["x1"] - image["x0"]) * (image["bottom"] - image["top"]),
            )
            text_overlap = sum(
                overlap_area(image, (word["x0"], word["top"], word["x1"], word["bottom"]))
                for word in words
            )
            records.append(
                {
                    "object": image["name"],
                    "bbox": [
                        round(image["x0"], 3),
                        round(image["top"], 3),
                        round(image["x1"], 3),
                        round(image["bottom"], 3),
                    ],
                    "display_size": [
                        round(image["x1"] - image["x0"], 3),
                        round(image["bottom"] - image["top"], 3),
                    ],
                    "source_size": list(image["srcsize"]),
                    "text_overlap_ratio": round(min(1.0, text_overlap / area), 6),
                    "bits": image.get("bits"),
                }
            )
        return records


def extract_embedded(
    pdf_path: Path,
    page_index: int,
    object_name: str,
    output_path: Path,
) -> tuple[int, int]:
    page = PdfReader(pdf_path).pages[page_index]
    matches = [
        item
        for item in page.images
        if item.name.rsplit(".", 1)[0] == object_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one image object {object_name}, found {len(matches)}"
        )
    image = Image.open(BytesIO(matches[0].data)).convert("RGBA")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return image.size


def render_page(pdf_path: Path, page_number: int, dpi: int, destination: Path) -> None:
    command = [
        shutil.which("pdftoppm") or "pdftoppm",
        "-f",
        str(page_number),
        "-l",
        str(page_number),
        "-png",
        "-r",
        str(dpi),
        "-singlefile",
        str(pdf_path),
        str(destination.with_suffix("")),
    ]
    subprocess.run(command, check=True)
    if not destination.exists():
        raise FileNotFoundError(f"Page rendering failed: {destination}")


def extract_crop(
    page_image_path: Path,
    box: list[float],
    dpi: int,
    output_path: Path,
) -> tuple[int, int]:
    scale = dpi / 72
    image = Image.open(page_image_path).convert("RGB")
    pixel_box = tuple(round(value * scale) for value in box)
    crop = image.crop(pixel_box)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(output_path)
    return crop.size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--page", type=int, required=True, help="One-based page number")
    parser.add_argument("--output", required=True)
    parser.add_argument("--selections")
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    page_index = args.page - 1

    audit = build_audit(pdf_path, page_index)
    audit_path = output / "audit.json"
    audit_path.write_text(
        json.dumps(
            {
                "pdf": str(pdf_path),
                "page": args.page,
                "image_object_count": len(audit),
                "images": audit,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"audit={audit_path}")
    if args.audit_only or not args.selections:
        return

    selection_data = json.loads(Path(args.selections).read_text(encoding="utf-8"))
    items = selection_data["items"]
    source_dir = output / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    with tempfile.TemporaryDirectory(prefix="pdf-assets-") as temp_name:
        temp = Path(temp_name)
        rendered = {}
        for item in items:
            name = item["name"]
            kind = item["kind"]
            destination = source_dir / f"{name}.png"
            if kind == "embedded":
                width, height = extract_embedded(
                    pdf_path, page_index, item["object"], destination
                )
                method = "embedded_image"
            elif kind == "crop":
                dpi = int(item.get("dpi", 600))
                if dpi not in rendered:
                    render_path = temp / f"page-{args.page}-{dpi}.png"
                    render_page(pdf_path, args.page, dpi, render_path)
                    rendered[dpi] = render_path
                width, height = extract_crop(
                    rendered[dpi], item["box"], dpi, destination
                )
                method = "page_crop"
            else:
                raise ValueError(f"Unsupported selection kind: {kind}")

            manifest.append(
                {
                    "name": name,
                    "source_pdf": str(pdf_path),
                    "source_page": args.page,
                    "source_kind": method,
                    "selection": item,
                    "width": width,
                    "height": height,
                    "file": str(destination),
                }
            )

    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"asset_count": len(manifest), "assets": manifest},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"assets={len(manifest)}")
    print(f"manifest={manifest_path}")


if __name__ == "__main__":
    main()
