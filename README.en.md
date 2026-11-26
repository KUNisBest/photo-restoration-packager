# Photo Restoration Packager

[English](README.en.md) | [简体中文](README.md)

An Agent skill and deterministic toolkit for restoring low-resolution photos,
extracting artwork from PDFs, and packaging the results with provenance.

The project focuses on a common failure mode: a document or card is not a
high-resolution image pack, but the visible art is only 90-330 pixels wide.
Blindly upscaling the whole page makes text unreliable and generates details
that did not exist. This project separates source extraction, vector rendering,
AI-assisted upscaling, validation, and packaging.

## What it does

- Restores standalone photos with the official portable Real-ESRGAN build.
- Audits PDF image objects, their page positions, source dimensions, and text
  overlap before processing.
- Extracts an explicit allowlist of text-free embedded images.
- Renders vector/image groups at a chosen DPI.
- Avoids applying AI a second time to already high-resolution composites.
- Generates manifests, source/final contact sheets, and a verified ZIP.
- Keeps the original files untouched.

## Why an allowlist

OCR can miss labels baked into raster art. The safest workflow is:

1. Audit a page.
2. Visually review text-free asset groups.
3. Write an allowlist of embedded objects or crop boxes.
4. Process only that allowlist.
5. Verify counts, dimensions, and the final archive.

This prevents captions, numbers, room names, logos, or instructional callouts
from entering a generative upscaler.

## Requirements

- Python 3.11 or newer
- Pillow
- pypdf
- pdfplumber
- Poppler `pdftoppm`
- Optional: Vulkan-capable GPU. The official NCNN build works on CPU as well,
  but is much slower.

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install Poppler so `pdftoppm` is on `PATH`. On Windows, you can use a Poppler
distribution such as the one bundled with many document tools.

## Use as a Codex skill

Copy this repository directory to your Codex skills directory:

```powershell
Copy-Item . "$HOME\.codex\skills\photo-restoration-packager" -Recurse
```

Restart Codex or start a new task so the skill metadata is reloaded.

Example requests:

```text
Make this scanned photo clearer without changing facial identity, preserve the
original, and package both versions.
```

```text
Audit page 2 of this PDF, extract only approved text-free artwork, upscale the
small raster assets, and produce a verified ZIP.
```

## CLI workflow

### 1. Audit a PDF page

```powershell
python scripts/extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work/pdf-assets `
  --audit-only
```

Review `work/pdf-assets/audit.json` and the rendered page.

### 2. Create an allowlist

Start from [references/allowlist.example.json](references/allowlist.example.json):

```json
{
  "items": [
    {
      "name": "story_tile",
      "kind": "embedded",
      "object": "Im59"
    },
    {
      "name": "visitor_pawns",
      "kind": "crop",
      "box": [145.0, 520.0, 248.0, 561.7],
      "dpi": 600
    }
  ]
}
```

`embedded` extracts the original PDF image object. `crop` renders a PDF page at
the requested DPI and crops the page-coordinate box with a top-left origin.

### 3. Extract approved assets

```powershell
python scripts/extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work/pdf-assets `
  --selections selections.json
```

### 4. Upscale only small raster assets

```powershell
python scripts/restore_assets.py `
  --input work/pdf-assets/source `
  --output work/pdf-assets/enhanced-4x `
  --scale 4 `
  --tile 512
```

The script downloads the official portable Real-ESRGAN NCNN release into a
temporary tool directory if it is missing. You can select a specific Vulkan
device with `--gpu`.

Do not include 600-dpi vector composites in this batch. Keep them in a separate
`vector-renders/` directory.

### 5. Package and verify

Create source and final contact sheets:

```powershell
python scripts/make_contact_sheet.py `
  --input work/pdf-assets/source `
  --output work/pdf-assets/contact-source.png

python scripts/make_contact_sheet.py `
  --input work/pdf-assets/enhanced-4x work/pdf-assets/vector-renders `
  --output work/pdf-assets/contact-final.png
```

Review both sheets, then package:

```powershell
python scripts/package_results.py `
  --root work/pdf-assets `
  --zip outputs/restored-assets.zip
```

The packager writes `qa-report.json`, checks ZIP CRCs, and reports the archive
SHA256.

## Expected output

```text
output/
  source/
  enhanced-4x/
  vector-renders/
  contact-source.png
  contact-final.png
  manifest.json
  qa-report.json
  README.md
```

An Agent should inspect the generated contact sheets before packaging, so that
text-bearing images and failed upscales are caught visually.

## Fidelity policy

- Use `source extract` for unchanged decoded source pixels.
- Use `AI-assisted upscale` for Real-ESRGAN output.
- Use `vector re-render` for PDF text and shapes rendered at higher DPI.
- Never call AI-generated texture "recovered detail".
- Never label a reconstruction as official artwork without owner confirmation.
- For faces, review identity separately from sharpness.
- For formal documents, rebuild text and vector layers instead of upscaling a
  page screenshot.

See [references/fidelity-policy.md](references/fidelity-policy.md) and
[references/pdf-asset-workflow.md](references/pdf-asset-workflow.md).

## Tests

```powershell
python tests/smoke_test.py
```

The test:

- validates `SKILL.md` frontmatter
- compiles all Python scripts
- packages synthetic images
- verifies ZIP integrity and required entries

GPU execution is intentionally excluded from CI.

## Third-party projects

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN): BSD-3-Clause
- [GFPGAN](https://github.com/TencentARC/GFPGAN): Apache-2.0
- [SUPIR](https://github.com/Fanghua-Yu/SUPIR): non-commercial use without
  separate permission

See [THIRD_PARTY.md](THIRD_PARTY.md).

## License

This project is licensed under the [MIT License](LICENSE).
