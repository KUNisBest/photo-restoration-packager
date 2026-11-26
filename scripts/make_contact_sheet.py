#!/usr/bin/env python3
"""Create a labeled contact sheet for one or more image directories."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--cell-width", type=int, default=320)
    parser.add_argument("--cell-height", type=int, default=360)
    args = parser.parse_args()

    images = []
    for directory in args.input:
        path = Path(directory)
        images.extend(
            sorted(
                item
                for item in path.iterdir()
                if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES
            )
        )
    if not images:
        raise RuntimeError("No images found")

    rows = (len(images) + args.columns - 1) // args.columns
    sheet = Image.new(
        "RGB",
        (args.columns * args.cell_width, rows * args.cell_height),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)

    for index, path in enumerate(images):
        x = (index % args.columns) * args.cell_width
        y = (index // args.columns) * args.cell_height
        with Image.open(path) as image:
            preview = image.convert("RGBA")
            original_size = image.size
        preview.thumbnail(
            (args.cell_width - 24, args.cell_height - 70),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGBA", preview.size, "white")
        canvas.alpha_composite(preview)
        sheet.paste(canvas.convert("RGB"), (x + 12, y + 12))
        draw.text(
            (x + 12, y + args.cell_height - 52),
            path.stem,
            fill="black",
            font=font,
        )
        draw.text(
            (x + 12, y + args.cell_height - 28),
            f"{original_size[0]}x{original_size[1]}",
            fill="#555555",
            font=font,
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(f"images={len(images)}")
    print(f"contact_sheet={output.resolve()}")


if __name__ == "__main__":
    main()
