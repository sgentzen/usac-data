# Releasing

`usac-data` publishes to PyPI from `.github/workflows/release.yml`, using PyPI
Trusted Publishing. No PyPI API token is stored in this repository.

The workflow triggers on **published GitHub Release** only — pushing a tag by
itself does nothing. This is deliberate: publishing to PyPI is irreversible
(a version number can never be reused, even after deletion), so it takes an
explicit action rather than happening as a side effect of tagging.

## One-time setup

Until this is done, the workflow will run and fail at the publish step.

1. **Register the pending publisher on PyPI.** The project does not exist on
   PyPI yet, so use the *pending* publisher form at
   <https://pypi.org/manage/account/publishing/>:

   | Field | Value |
   |-------|-------|
   | PyPI project name | `usac-data` |
   | Owner | `sgentzen` |
   | Repository name | `usac-data` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

   The pending publisher converts to a normal one on first successful upload.

2. **Create the `pypi` environment** in repository Settings → Environments.
   The name must match the workflow's `environment.name` exactly. Adding
   required reviewers there gives a manual approval gate before anything
   reaches PyPI — recommended.

## Cutting a release

1. Bump the version in **both** places — they are checked against the tag and a
   mismatch fails the build:
   - `pyproject.toml` → `[project] version`
   - `src/usac_data/__init__.py` → `__version__`

2. Move the `[Unreleased]` section of `CHANGELOG.md` under the new version
   heading with today's date.

3. Merge that to `master` and confirm CI is green.

4. Tag and push:

   ```bash
   git tag -a v0.1.6 -m "v0.1.6"
   git push origin v0.1.6
   ```

5. Publish a GitHub Release for the tag. That starts the workflow.

The tag may be written `v0.1.6` or `0.1.6`; the leading `v` is stripped before
comparison.

## What the workflow checks

- **Version agreement** — the tag, `pyproject.toml` and `__version__` must all
  match. These have drifted before: `__version__` sat at `0.1.2` while
  `pyproject.toml` had moved to `0.1.4`. Shipping that mismatch would put a
  wheel on PyPI reporting a version different from the tag it was built from,
  and it could not be corrected in place.
- **Metadata validity** — `twine check` on both the sdist and the wheel before
  anything is uploaded.

Build and publish are separate jobs. Only the publish job holds `id-token:
write`, so the OIDC credential is not exposed to the build.

## Verifying a build locally

```bash
uv build
uv tool run --from "twine==6.2.0" --with "packaging==26.2" twine check dist/*
```

`packaging>=24.2` matters: this project uses PEP 639 (`license = "Apache-2.0"`),
so the build emits Metadata 2.4 with `License-Expression` and `License-File`.
Older `packaging` versions do not recognize those fields and `twine check`
reports `InvalidDistribution` on a distribution that is actually fine. If you
hit that error, check `packaging`'s version before suspecting the package.
