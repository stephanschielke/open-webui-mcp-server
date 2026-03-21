# Publishing Guide for open-webui-mcp-server

This guide covers the complete release process for publishing to PyPI, including setup, guardrails, and step-by-step instructions.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Pre-Release Checklist](#pre-release-checklist)
- [OIDC Trusted Publishing Setup](#oidc-trusted-publishing-setup)
- [Release Workflow](#release-workflow)
- [Guardrails](#guardrails)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Workflow Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐  │
│  │    Build     │────▶│  Upload Artifact │────▶│  publish-   │  │
│  │  (on push)   │     │  (dist/*)        │     │  dev        │  │
│  └──────────────┘     └──────────────────┘     │  (Test PyPI)│  │
│                                                └─────────────┘  │
│                           │                                     │
│                           ▼                                     │
│                    ┌──────────────────┐                         │
│                    │  publish-release │                         │
│                    │  (on tag v*)     │                         │
│                    │  → PyPI.org      │                         │
│                    └──────────────────┘                         │
│                           │                                     │
│                           ▼                                     │
│                    ┌──────────────────┐                         │
│                    │  create-release  │                         │
│                    │  (GitHub Release)│                         │
│                    └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component         | Purpose                              | Trigger            |
|-------------------|--------------------------------------|--------------------|
| `build`           | Build wheel and sdist distributions  | Every push to main |
| `publish-dev`     | Publish dev version to Test PyPI     | Every push to main |
| `publish-release` | Publish release to PyPI              | Tag push `v*`      |
| `create-release`  | Create GitHub Release with changelog | Tag push `v*`      |

---

## Pre-Release Checklist

Before creating a release, verify:

### 1. Code Quality

- [ ] All tests pass: `mise run owu:tests:all`
- [ ] Linter passes: `mise run owu:linter:check`
- [ ] No uncommitted changes: `git status`

### 2. Version Management

- [ ] Version in `pyproject.toml` is correct
- [ ] Version follows semantic versioning (MAJOR.MINOR.PATCH)
- [ ] CHANGELOG.md is updated (if using)

### 3. Documentation

- [ ] README.md is up to date
- [ ] API documentation reflects changes
- [ ] Breaking changes are documented

### 4. Dependencies

- [ ] `uv.lock` is up to date: `uv lock`
- [ ] No security vulnerabilities in dependencies

---

## OIDC Trusted Publishing Setup

### Why OIDC?

| Aspect              | API Tokens                | OIDC Trusted Publishing  |
|---------------------|---------------------------|--------------------------|
| **Lifespan**        | Long-lived (months/years) | Short-lived (max 15 min) |
| **Secret Required** | Yes                       | No                       |
| **Rotation**        | Manual                    | Automatic                |
| **Leak Risk**       | High                      | Low                      |
| **Audit Trail**     | Limited                   | Full (repo/workflow/env) |

### Setup Steps

#### 1. Configure PyPI Trusted Publisher

1. Go to https://pypi.org/manage/project/openwebui-mcp-server/settings/publishing/
2. Add a new trusted publisher:
    - **Owner**: `stephanschielke`
    - **Repository**: `open-webui-mcp-server`
    - **Workflow name**: `publish.yml`
    - **Environment name**: `pypi`

#### 2. Configure Test PyPI Trusted Publisher

1. Go to https://test.pypi.org/manage/project/openwebui-mcp-server/settings/publishing/
2. Add a new trusted publisher:
    - **Owner**: `stephanschielke`
    - **Repository**: `open-webui-mcp-server`
    - **Workflow name**: `publish.yml`
    - **Environment name**: `test.pypi`

#### 3. Verify GitHub Environment

The `pypi` environment should have:
- **Required reviewers**: At least one maintainer
- **Deployment branches**: Only `main` branch
- **No secrets needed** (OIDC handles authentication)

#### 4. Remove API Token (After Verification)

Once OIDC is working:
1. Revoke `PYPI_ACCOUNT_API_TOKEN` from PyPI
2. Remove secret from GitHub environment
3. Update workflow to use OIDC (no credentials)

---

## Release Workflow

### Step 1: Prepare Release

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Run tests and linter
mise run owu:tests:all
mise run owu:linter:check

# Bump version (choose one)
mise run bump:patch  # 0.2.0 -> 0.2.1
mise run bump:minor  # 0.2.0 -> 0.3.0
mise run bump:major  # 0.2.0 -> 1.0.0

# Review changes
git diff pyproject.toml
```

### Step 2: Commit and Tag

```bash
# Commit version bump
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"

# Create annotated tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Push commit and tag
git push origin main
git push origin vX.Y.Z
```

### Step 3: Monitor Release

1. Watch GitHub Actions: https://github.com/stephanschielke/open-webui-mcp-server/actions
2. Approve deployment when prompted (if environment protection is enabled)
3. Verify PyPI upload: https://pypi.org/project/openwebui-mcp-server/

### Step 4: Verify Installation

```bash
# Wait a few minutes for PyPI to process
pip install openwebui-mcp-server==X.Y.Z

# Or with uv
uv pip install openwebui-mcp-server==X.Y.Z

# Verify
openwebui-mcp --version
```

---

## Guardrails

### Environment Protection

The `pypi` environment has:
- **Required reviewers**: Prevents unauthorized deployments
- **Branch policy**: Only `main` branch can deploy
- **Manual approval**: Human must approve before publish

### Workflow Conditions

```yaml
publish-release:
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
```

This ensures:
- Only tag pushes trigger production releases
- Regular commits to main only publish to Test PyPI
- Pull requests don't trigger any publishing

### Artifact Integrity

- Artifacts are built once in the `build` job
- Same artifacts are used for both Test PyPI and production
- SHA256 hashes are printed during upload
- Attestations are generated for supply chain security

### Concurrency Control

```yaml
concurrency:
  group: ${{ github.sha }}
  cancel-in-progress: true
```

This prevents:
- Parallel releases from the same commit
- Race conditions in artifact uploads
- Duplicate package versions

---

## Troubleshooting

### Issue: "OIDC token request failed"

**Cause**: Trusted publisher not configured on PyPI

**Solution**:
1. Verify trusted publisher settings on PyPI
2. Ensure workflow name matches exactly (`publish.yml`)
3. Ensure environment name matches (`pypi`)

### Issue: "Version already exists on PyPI"

**Cause**: Trying to publish a version that already exists

**Solution**:
1. Bump version in `pyproject.toml`
2. Create new tag with updated version
3. Never reuse version numbers

### Issue: "Environment protection rule failed"

**Cause**: Deployment blocked by environment protection

**Solution**:
1. Check if you're a required reviewer
2. Approve the deployment in GitHub Actions UI
3. Verify you're deploying from `main` branch

### Issue: "Artifact not found"

**Cause**: Build job failed or artifact expired

**Solution**:
1. Check build job logs for errors
2. Re-run the workflow if artifact expired
3. Verify artifact name matches (`python-package-distributions`)

### Issue: "Package installation fails after publish"

**Cause**: PyPI needs time to process the upload

**Solution**:
1. Wait 5-10 minutes for PyPI CDN to update
2. Clear pip cache: `pip cache purge`
3. Try installing with `--no-cache-dir`

---

## Rollback Procedure

If a bad release is published:

### 1. Yank the Release (Preferred)

```bash
# Install twine if not present
pip install twine

# Yank the release (makes it unavailable for new installs)
twine yank openwebui-mcp-server==X.Y.Z

# Note: Existing installations can still use yanked versions
# You must explicitly uninstall and reinstall
```

### 2. Publish Hotfix

```bash
# Fix the issue
# Bump patch version
mise run bump:patch

# Commit and tag
git add pyproject.toml
git commit -m "fix: hotfix for vX.Y.Z"
git tag -a vX.Y.(Z+1) -m "Hotfix release vX.Y.(Z+1)"
git push origin main vX.Y.(Z+1)
```

### 3. Notify Users

- Create GitHub issue explaining the problem
- Update README with known issues
- Post announcement if critical

---

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
