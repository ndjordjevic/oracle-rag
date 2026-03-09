# How to create a release

Short checklist for cutting a new **oracle-rag** version (GitHub Release + PyPI).

## 1. Bump version and push

- In `pyproject.toml`, set `version = "X.Y.Z"`.
- Commit and push:
  ```bash
  git add pyproject.toml && git commit -m "Bump version to X.Y.Z" && git push origin main
  ```

## 2. Tag and push

- Create an annotated tag and push it:
  ```bash
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push origin vX.Y.Z
  ```
- If you need to publish to PyPI manually: `uv build && uv publish` (use PyPI API token when prompted).

## 3. GitHub Release with notes (triggers PyPI publish)

- Creating and **publishing** the release runs the workflow and publishes to PyPI. Tag push alone does not publish.

- **Option A — create with notes:**  
  ```bash
  gh release create vX.Y.Z --notes "PASTE_NOTES_HERE"
  ```
- **Option B — create then edit:**  
  ```bash
  gh release create vX.Y.Z --notes "Placeholder"
  gh release edit vX.Y.Z --notes "PASTE_NOTES_HERE"
  ```

### Release notes format

Match existing releases (see [Releases](https://github.com/ndjordjevic/oracle-rag/releases)):

1. **Title:** `# vX.Y.Z — Short subtitle`
2. **Summary:** One line describing the release (e.g. “Evaluation framework, Cohere reranking, and config defaults since v3.0.1.”).
3. **Sections:** `## Section name` (e.g. Configuration, Evaluation, Docs, Package).
4. **Bullets:** `- **Topic** — Detail.`

To draft notes from the diff:

```bash
git log vPREV..vX.Y.Z --oneline   # e.g. v3.0.1..v3.1.0
git diff vPREV..vX.Y.Z --stat    # what files changed
```

Write the notes from the actual changes, then paste into `gh release create` or `gh release edit`.
