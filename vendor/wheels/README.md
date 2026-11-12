# Vendored clients of the AI Fabric

Wheels of the owner's AI Fabric clients (here `fabric-ocr`, the OCR service's client), copied from the Fabric's
package index (home network only, address in `honzapetr/aiops-homelab`) - so CI and the image build need no access to
the homelab. `pyproject.toml` pins each client to this folder (an explicit uv index `fabric-vendor`), so no package of
the same name from PyPI can replace it. Design: ADR 0005.

Never edit a wheel. A newer version: download it from the index (check its `sha256` on the index page), delete the old
wheel, raise the version in `pyproject.toml`, run `uv lock` (uv >= 0.13) and commit all three together.
