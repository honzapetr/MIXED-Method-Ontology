# Vendored clients of the AI Fabric

Wheels of the owner's AI Fabric clients (here `fabric-ocr`, the OCR service's client), copied from the Fabric's
package index (home network only, address in `honzapetr/aiops-homelab`) - so CI and the image build need no access to
the homelab. `pyproject.toml` pins each client to its wheel file in this folder (`tool.uv.sources`, a path), so no package of
the same name from PyPI can replace it. A path, not a flat index: uv resolves a relative index against the folder
it runs in, so a study using this project as a path dependency could not find it (ADR 0010). Design: ADR 0005.

Never edit a wheel. A newer version: download it from the index (check its `sha256` on the index page), delete the old
wheel, change the file name and the version in `pyproject.toml`, run `uv lock` (uv >= 0.13) and commit all three together.
