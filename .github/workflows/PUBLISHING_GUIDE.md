# Publishing Guide for open-webui-mcp-server

This guide covers the complete release process for publishing to PyPI, including setup, guardrails, and step-by-step instructions.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [OIDC Trusted Publishing Setup](#oidc-trusted-publishing-setup)
- [Release Workflow](#release-workflow)
- [Security Guardrails](#security-guardrails)
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
│  └──────────────┘     └──────────────────┘     │ (Test PyPI) │  │
│                                                └─────────────┘  │
│                           │                                     │
│                           ▼                                     │
│                    ┌──────────────────┐                         │
│                    │  publish-release │                         │
│                    │  (on tag v*)     │                         │
│                    │  → PyPI.org      │                         │
│                    │  (OIDC)          │                         │
│                    └──────────────────┘                         │
│                           │                                     │
│                           ▼                                     │
│                    ┌──────────────────┐                         │
│                    │  create-release  │                         │
│                    │ (GitHub Release) │                         │
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

## Prerequisites

### PyPI Account

1. Create an account on [pypi.org](https://pypi.org/)
2. Verify your email address
3. Enable 2FA for security

### GitHub Environment

The `pypi` environment must be configured with:

1. **Required reviewers**: At least one maintainer
2. **Deployment branches**: Only `main` branch
3. **Deployment tags**: Pattern `v*`

Configure at: https://github.com/stephanschielke/open-webui-mcp-server/settings/environments

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

1. Go to: https://pypi.org/manage/project/openwebui-mcp-server/settings/publishing/
2. Add a new trusted publisher:
    - **Owner**: `stephanschielke`
    - **Repository**: `open-webui-mcp-server`
    - **Workflow name**: `publish.yml`
    - **Environment name**: `pypi`

#### 2. Configure Test PyPI Trusted Publisher

1. Go to: https://test.pypi.org/manage/project/openwebui-mcp-server/settings/publishing/
2. Add a new trusted publisher:
    - **Owner**: `stephanschielke`
    - **Repository**: `open-webui-mcp-server`
    - **Workflow name**: `publish.yml`
    - **Environment name**: `test.pypi`

#### 3. Verify GitHub Environment

The `pypi` environment should have:
- **Required reviewers**: At least one maintainer
- **Deployment branches**: Only `main` branch
- **Deployment tags**: Pattern `v*`
- **No secrets needed** (OIDC handles authentication)

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
```

### Step 2: Create Release

```bash
# Option A: Automated (recommended)
mise run release:prepare 0.2.1

# Option B: Manual
mise run bump:patch
git add pyproject.toml
git commit -m "chore: bump version to 0.2.1"
git tag -a v0.2.1 -m "Release v0.2.1"
git push origin main v0.2.1
```

### Step 3: Monitor Release

1. Watch GitHub Actions: https://github.com/stephanschielke/open-webui-mcp-server/actions
2. Approve deployment when prompted (if environment protection is enabled)
3. Verify PyPI upload: https://pypi.org/project/openwebui-mcp-server/

### Step 4: Verify Installation

```bash
# Wait a few minutes for PyPI to process
pip install openwebui-mcp-server==0.2.1

# Or with uv
uv pip install openwebui-mcp-server==0.2.1

# Verify
openwebui-mcp --version
```

---

## Security Guardrails

### Environment Protection

The `pypi` environment has:
- **Required reviewers**: Prevents unauthorized deployments
- **Branch policy**: Only `main` branch can deploy
- **Tag policy**: Only `v*` tags can deploy
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
  group: release-${{ github.sha }}
  cancel-in-progress: false # Never cancel production releases
```

This prevents:
- Parallel releases from the same commit
- Race conditions in artifact uploads
- Duplicate package versions

---

## Mise Tasks

### Release Tasks

```bash
# Run pre-release checks (tests, linter, build)
mise run release:check

# Create and push a release tag
mise run release:tag 0.2.1

# Full release preparation (checks + tag)
mise run release:prepare 0.2.1
```

### Build Tasks

```bash
# Build wheel and sdist
mise run build

# Bump version
mise run bump:patch
mise run bump:minor
mise run bump:major
```

### Test Tasks

```bash
# Run all tests
mise run owu:tests:all

# Run unit tests only
mise run owu:tests:unit

# Run integration tests
mise run owu:tests:integration
```

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
3. Verify you're deploying from `main` branch with a `v*` tag

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
twine yank openwebui-mcp-server==0.2.1

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
git commit -m "fix: hotfix for 0.2.1"
git tag -a v0.2.2 -m "Hotfix release v0.2.2"
git push origin main v0.2.2
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
- [Mise Task Arguments](https://mise.jdx.dev/tasks/task-arguments.html)
