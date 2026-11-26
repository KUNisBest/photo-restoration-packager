# Security

This project processes local files and downloads the official Real-ESRGAN
portable release from GitHub.

## Reporting

Please report security concerns privately to the repository owner after the
public repository is created. Do not include private images, documents, tokens,
or personal paths in a public issue.

## Scope

The scripts:

- do not upload input images
- do not send document content to a model service
- write only to paths supplied by the user
- download only from the pinned official Real-ESRGAN release URL

Users should still review commands before processing sensitive material.
