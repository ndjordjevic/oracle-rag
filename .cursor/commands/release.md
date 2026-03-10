# Release oracle-rag

Cut a new oracle-rag release: bump version, tag, push, and create a GitHub Release (which triggers PyPI publish).

## Steps

1. **Determine version** — If the user provides a version (e.g. `0.7.0`), use it. Otherwise read `pyproject.toml` and suggest the next patch (e.g. `0.6.0` → `0.6.1`) or ask the user.

2. **Bump version** — In `pyproject.toml`, set `version = "X.Y.Z"`.

3. **Commit and push** — Run:
   ```bash
   git add pyproject.toml && git commit -m "Bump version to X.Y.Z" && git push origin main
   ```

4. **Tag and push** — Run:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

5. **Create GitHub Release** — Run:
   ```bash
   gh release create vX.Y.Z --notes "Placeholder"
   ```
   Then edit with real notes:
   ```bash
   gh release edit vX.Y.Z --notes "PASTE_NOTES_HERE"
   ```
   Or create with notes in one step if the user provides them.

6. **Release notes format** — Match existing releases. Scan all commits and changes from the previous release to draft notes:
   - Title: `# vX.Y.Z — Short subtitle`
   - Summary: One line describing the release.
   - Sections: `## Section name` (e.g. Configuration, Evaluation, Docs).
   - Bullets: `- **Topic** — Detail.`
   - To draft from diff: `git log vPREV..vX.Y.Z --oneline` and `git diff vPREV..vX.Y.Z --stat`

## Notes

- Publishing the GitHub Release runs the workflow and publishes to PyPI. Tag push alone does not publish.
- If `gh` is not available or the user prefers manual PyPI: `uv build && uv publish` (use PyPI API token when prompted).
- Ensure you are on `main` and have no uncommitted changes before starting.
