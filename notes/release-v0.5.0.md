# v0.5.0 — PyPI publish on release

CI: PyPI publish is now triggered when a GitHub Release is **published**, not on tag push. Tag and push as before, then create the release; publishing the release runs the workflow and uploads to PyPI.

## CI

- **Publish workflow** — Trigger changed from `push: tags: v*.*.*` to `release: types: [published]`; checkout uses the release’s tag so the correct version is built and published.

## Docs

- **how-to-release** — Step 3 clarified: publishing the GitHub Release triggers PyPI publish; tag push alone does not.
