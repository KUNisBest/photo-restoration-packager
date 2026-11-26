# Contributing

Thanks for improving Photo Restoration Packager.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tests\smoke_test.py
```

## Pull requests

- Keep the original input untouched.
- Add a test for changes to extraction, upscaling orchestration, or packaging.
- Do not add sample PDFs, restored artwork, or photos unless their license
  explicitly permits redistribution.
- Document whether an output is a source extract, AI-assisted upscale, or vector
  re-render.
- Do not make text or critical labels pass through a generative upscaler by
  default.

## Reporting issues

Include:

- operating system and GPU
- Python version
- source image dimensions
- command line
- sanitized error output

Do not attach private documents or personal photos to a public issue.
