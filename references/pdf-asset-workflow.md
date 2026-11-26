# PDF Asset Workflow

## Audit before extraction

Run the page audit and inspect the rendered page. Distinguish:

- native text and vector shapes
- embedded raster objects
- raster objects used as masks, shadows, or highlights
- images whose final look is assembled from multiple layers
- labels baked into the raster

A PDF may contain hundreds of image objects for one page. One visible thumbnail
can be split across several objects. Extract only after understanding the group.

## Allowlist

Use an explicit JSON allowlist for text-free images. The agent can prepare it
from visual review, but the user should review it when "official accuracy" is
required.

```json
{
  "items": [
    {"name": "example", "kind": "embedded", "object": "Im59"},
    {
      "name": "group",
      "kind": "crop",
      "box": [10.0, 20.0, 100.0, 80.0],
      "dpi": 600
    }
  ]
}
```

Coordinates use PDF points with the top-left origin, matching pdfplumber.

## Common mistakes

- Taking one page screenshot and enlarging it
- Treating a 600-dpi vector composite as a low-resolution raster
- Extracting only shadow or mask layers
- Including room names or numbers baked into artwork
- Running AI over captions
- Forcing a discrete GPU without checking whether large composite assets fit
- Delivering a ZIP without testing its central directory and CRCs
