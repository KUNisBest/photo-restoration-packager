---
name: photo-restoration-packager
description: Restore or upscale low-resolution photos and extract or enhance artwork from PDFs. Use this skill whenever the user mentions making a photo clearer, blurry or low-resolution images, old-photo restoration, super-resolution, Real-ESRGAN, GFPGAN, low-res card or illustration assets embedded in a PDF, separating images from text, or packaging restored assets into a repeatable deliverable. Also use it when the user asks whether AI enhancement is faithful, wants to prevent text from being altered, or wants a reusable ZIP pipeline. 中文请求涉及照片变清晰、老照片修复、图片超分、模糊图片、PDF 内嵌小图、排除文字、素材放大或打包 ZIP 时也必须使用。
compatibility: Windows is the primary target. Requires Python 3.11+, Pillow, pypdf, pdfplumber, Poppler pdftoppm, and optionally an NVIDIA or other Vulkan-capable GPU.
---

# Photo Restoration and Asset Packaging

Respond in the user's language. When the user writes in Chinese, use Chinese
section names, status messages, provenance labels, and final explanations while
keeping command-line flags unchanged.

Start by deciding what must remain faithful. "Make it clearer" can mean three
different jobs, and mixing them produces misleading output:

1. **Fidelity restoration**: remove compression/noise and enlarge with minimal
   invention. Use this for photos with text, evidence, archival value, or exact
   artwork.
2. **AI upscaling**: make small art look sharper. Real-ESRGAN is appropriate,
   but it can invent texture and must be labeled as AI-assisted.
3. **Generative reconstruction**: redraw severely damaged or very small imagery.
   Use only with explicit permission and never present the result as official or
   exact.

Preserve the original file. Write outputs into new files and record the method
used.

## Choose the workflow

### Standalone photo

1. Inspect dimensions, blur, noise, and whether faces or text are present.
2. For general photos, use Real-ESRGAN with a conservative scale. Start at 2x
   when the source already has visible noise or compression artifacts.
3. For faces, run Real-ESRGAN first and use GFPGAN separately only when the user
   accepts possible identity changes. Never present face restoration as exact.
4. For severely damaged old photos, SUPIR may be useful, but it is large,
   slower, and non-commercial without separate permission. Generate variants
   instead of overwriting the source.
5. For text, documents, or official artwork, do not use generative upscaling on
   the text-bearing area. Rebuild text or retain the original raster.

### PDF or card artwork

Do not screenshot a low-resolution card and upscale the whole page. First audit
the PDF objects:

1. Render the relevant page for visual review.
2. List embedded raster image objects and their native source dimensions.
3. List text blocks and image bounding boxes.
4. Re-render vector and text layers at the requested output size.
5. Extract raster art at native resolution.
6. Render image groups that are assembled from PDF vector and raster layers at a
   sufficiently high DPI.
7. Exclude images that contain text, numbers, logos, or instructional callouts
   unless the user explicitly wants a reconstruction rather than an exact asset.
8. AI-upscale only the small raster objects that are genuinely low-resolution.
   Do not AI-upscale an already crisp vector composite.

Small-image inclusion requires visual judgment. OCR and text bounding boxes help
but cannot detect every label baked into a raster image. Build and review an
explicit allowlist before batch processing. See
`references/pdf-asset-workflow.md`.

## Use the bundled scripts

Resolve `<skill-root>` to the directory containing this `SKILL.md`.

### Audit a PDF page

```powershell
python <skill-root>\scripts\extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work\pdf-assets `
  --audit-only
```

Review `audit.json`. It lists source dimensions, page placement, text overlap,
and the rendered size. For decisions such as "exclude room boards because their
room names are baked into the images", inspect the rendered page or crops.

### Extract an approved allowlist

Create a selection JSON:

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

Then run:

```powershell
python <skill-root>\scripts\extract_pdf_assets.py `
  --pdf input.pdf `
  --page 2 `
  --output work\pdf-assets `
  --selections selections.json
```

The script writes `source/` and `manifest.json`. It never extracts the full page
as a substitute for real embedded or vector assets.

### Upscale approved small images

```powershell
python <skill-root>\scripts\restore_assets.py `
  --input work\pdf-assets\source `
  --output work\pdf-assets\enhanced-4x `
  --scale 4 `
  --tile 512 `
  --gpu 1
```

Omit `--gpu` to let Real-ESRGAN choose automatically. If the user has an NVIDIA
GPU and both integrated and discrete GPUs are present, inspect the Real-ESRGAN
device list and use the NVIDIA index. Reduce `--tile` if memory allocation fails.

Do not put 600-dpi vector composites through a second 4x AI pass. Copy them to a
separate `vector-renders/` directory.

### Package and validate

Create contact sheets for visual review:

```powershell
python <skill-root>\scripts\make_contact_sheet.py `
  --input work\pdf-assets\source `
  --output work\pdf-assets\contact-source.png

python <skill-root>\scripts\make_contact_sheet.py `
  --input work\pdf-assets\enhanced-4x work\pdf-assets\vector-renders `
  --output work\pdf-assets\contact-final.png
```

Inspect both sheets before packaging. Then run:

```powershell
python <skill-root>\scripts\package_results.py `
  --root work\pdf-assets `
  --zip outputs\restored-assets.zip
```

The packager creates a QA report and opens the resulting ZIP as a test. Report
the file count, archive size, and SHA256 in the final response.

## Output contract

Use this structure unless the user requests another:

```text
output/
  source/          Original-resolution extracts
  enhanced-4x/     AI-upscaled raster assets
  vector-renders/  High-DPI vector composites, not AI-upscaled
  contact-source.png
  contact-final.png
  manifest.json
  qa-report.json
  README.md
```

Every manifest record should include:

- stable asset name
- source page
- source kind (`embedded_image` or `page_crop`)
- original object name or page coordinates
- native dimensions
- final dimensions
- processing method
- whether the result is AI-reconstructed

## Fidelity and safety rules

- Keep originals untouched.
- Never claim AI-invented detail is recovered fact.
- Never label restored artwork as official unless the source owner confirms it.
- Do not run super-resolution over text, numbers, logos, or critical labels.
- If source art is only 90-100 px and the requested use is a formal full card,
  state that exact high-resolution artwork cannot be recovered from that input.
- For faces, preserve identity as a review criterion; synthetic sharpness is not
  equivalent to a faithful likeness.
- Respect model licenses. SUPIR is non-commercial without separate permission;
  Real-ESRGAN is BSD-3-Clause and GFPGAN is Apache-2.0.
- When the user asks for "official accuracy", prefer a rebuilt card system with
  original artwork, or request the original production assets.

## Verification

Before delivering:

1. Open source and final contact sheets.
2. Confirm no text-bearing thumbnails entered the allowlist.
3. Confirm source and final asset counts match or document intentional skips.
4. Check long edges and aspect ratios.
5. Test the ZIP CRC and ensure the final deliverable opens.
6. Include a concise provenance note and SHA256.

Read `references/fidelity-policy.md` when the request involves archival photos,
official artwork, faces, or claims of accuracy.
