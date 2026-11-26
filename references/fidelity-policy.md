# Fidelity Policy

## Language

Use precise labels:

- `source extract`: decoded from the original file without generative changes
- `AI-assisted upscale`: enlarged by a learned model; texture may be invented
- `AI-assisted reconstruction`: generative repair; detail is plausible, not proven
- `vector re-render`: text and vector shapes rendered from the source document at higher DPI

Do not call an AI result "recovered", "official", or "exact" without a verifiable
source.

## Model selection

Real-ESRGAN:

- Best default for general photos and isolated low-resolution artwork.
- Use 2x first on noisy, compressed, or already soft inputs.
- Use tiling for large images or limited VRAM.
- Do not apply to text layers or complete document pages.

GFPGAN:

- Face-only restoration after general upscaling.
- Warn that facial identity and expression can shift.

SUPIR:

- Strong for heavily degraded photos and prompt-guided reconstruction.
- High compute requirements.
- Non-commercial use only without separate permission.

Non-generative resize:

- Lanczos or bicubic can satisfy exact dimensions without fabricating detail.
- It will remain soft when the source is genuinely too small.

## Formal card workflow

When the requested output is a 1440x2160 card and the PDF only contains a
240-330 px thumbnail:

1. Audit whether text, frames, and icons are separate vector objects.
2. Extract artwork at native resolution.
3. Re-typeset text and rebuild vector frames.
4. Re-render those layers at the final dimensions.
5. Keep AI enhancement limited to isolated artwork where the user accepts
   reinterpretation.

If the entire card is one 240-330 px raster and the user requires official
accuracy, the required source does not exist in the supplied PDF.
