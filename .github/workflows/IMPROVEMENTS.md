# Workflow Improvements and Critical Analysis

This document addresses critical questions about the production publishing workflow and provides a comprehensive improvement plan.

## Critical Questions Answered

### 1. Tag Creation: Who creates `v*` tags?

**Answer**: Manual tag creation by maintainers (currently).

**Recommendation**: Add automated tag creation via mise tasks.

**Implementation**:
```bash
# New mise tasks added:
mise run release:prepare 0.2.0  # Runs checks, bumps version, creates tag
mise run release:tag 0.2.0      # Just creates the tag
mise run release:check          # Just runs pre-release checks
```

**When to create tags**:
- After all PRs for a release are merged to main
- After running `mise run release:check` successfully
- When you're ready to publish to production PyPI

**Guardrails**:
- Pre-release checks must pass
- No uncommitted changes
- Semantic versioning enforced
- Tag existence check

---

### 2. Artifact Visibility: Can we see artifacts?

**Answer**: Yes, artifacts are visible in GitHub Actions UI.

**Where to find them**:
1. Go to any workflow run: https://github.com/stephanschielke/open-webui-mcp-server/actions
2. Click on a completed workflow run
3. Scroll to "Artifacts" section at the bottom
4. Download `python-package-distributions`

**Artifact contents**:
- `dist/*.whl` - Built wheel distribution
- `dist/*.tar.gz` - Source distribution

**Retention**:
- Remote GitHub: 5 days
- Local act: 1 day

**Note**: Artifacts are only available for completed workflow runs. If a workflow is cancelled or fails, artifacts may not be available.

---

### 3. ghalint: Should it be a job or step?

**Answer**: It's now a step in the build job.

**Implementation**:
```yaml
- name: Validate workflow
  run: mise run owu:gha:lint
```

**Why as a step**:
- Catches workflow issues early
- No separate job overhead
- Fails fast if workflow has security issues
- Runs on every push

**Alternative**: Could be a separate job if you want to:
- Run it in parallel with build
- Have clearer separation of concerns
- Skip it in certain conditions

---

### 4. Rebuild: Do we need to rebuild with artifacts?

**Answer**: Yes, but only for production releases.

**Why we rebuild**:
1. The artifact from `build` job has the dev version (e.g., `0.2.0.dev1`)
2. For production, we need the release version (e.g., `0.2.0`)
3. We set the version from the tag, then rebuild

**Flow**:
```
build job → artifact (0.2.0.dev1)
                      ↓
publish-release job → download artifact → set version (0.2.0) → rebuild → publish
```

**Optimization opportunity**: We could build with the release version from the start if we detect a tag push. But this would complicate the build job logic.

**Current approach is correct** because:
- Build job runs on every push (needs dev version)
- Release job only runs on tags (needs release version)
- Rebuilding ensures correct version in package

---

### 5. OIDC vs API Token: Should we use OIDC?

**Answer**: Yes! OIDC is implemented.

**Current state**:
- Test PyPI: Already using OIDC (trusted publishing configured)
- Production PyPI: Now using OIDC (workflow updated)

**Migration path**:
1. ✅ Configure trusted publisher on PyPI
2. ✅ Update workflow to use OIDC (no credentials)
3. ⏳ Test with a release
4. ⏳ Remove `PYPI_ACCOUNT_API_TOKEN` secret after verification

**Security benefits**:

| Aspect          | API Token    | OIDC           |
|-----------------|--------------|----------------|
| Lifespan        | Months/years | 15 minutes max |
| Secret required | Yes          | No             |
| Rotation        | Manual       | Automatic      |
| Leak risk       | High         | Low            |
| Audit trail     | Limited      | Full           |

---

## Implementation Checklist

### Completed
- [x] Add ghalint validation to build job
- [x] Implement OIDC for production PyPI
- [x] Add version validation in publish-release job
- [x] Create GitHub Release job with changelog
- [x] Add mise tasks for release management
- [x] Create PUBLISH_GUIDE.md
- [x] Create RELEASE_CHECKLIST.md
- [x] Fix ghalint persist-credentials warning

### Pending (Requires Manual Action)
- [ ] Configure trusted publisher on PyPI.org
- [ ] Test OIDC with a release
- [ ] Remove `PYPI_ACCOUNT_API_TOKEN` after verification
- [ ] Add branch protection rules (if not already done)

---

## Security Guardrails Implemented

### 1. Environment Protection
- `pypi` environment requires manual approval
- Only `main` branch can deploy to production
- `test.pypi` has no protection (dev deployments)

### 2. Workflow Conditions
```yaml
publish-release:
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
```
- Only tag pushes trigger production releases
- Regular commits only publish to Test PyPI

### 3. OIDC Authentication
- No long-lived secrets
- Short-lived tokens (15 min max)
- Bound to specific repo/workflow/environment

### 4. Version Validation
```bash
if ! echo "$TAG_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: Version must follow semantic versioning"
  exit 1
fi
```

### 5. Pre-release Checks
```bash
mise run release:check  # Runs linter + tests + build
```

### 6. Concurrency Control
```yaml
concurrency:
  group: release-${{ github.sha }}
  cancel-in-progress: false  # Never cancel production releases
```

---

## Step-by-Step Production Release Guide

### Prerequisites (One-time Setup)

1. **Configure PyPI Trusted Publisher**:
    - Go to: https://pypi.org/manage/project/openwebui-mcp-server/settings/publishing/
    - Add trusted publisher:
        - Owner: `stephanschielke`
        - Repository: `open-webui-mcp-server`
        - Workflow: `publish.yml`
        - Environment: `pypi`

2. **Verify GitHub Environment**:
    - Go to: https://github.com/stephanschielke/open-webui-mcp-server/settings/environments
    - Ensure `pypi` environment has:
        - Required reviewers: At least one maintainer
        - Deployment branches: Only `main`

### Release Process

#### Step 1: Prepare Release (Local)

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Run pre-release checks
mise run release:check
```

#### Step 2: Create Release

```bash
# Option A: Automated (recommended)
mise run release:prepare 0.2.0

# Option B: Manual
mise run bump:patch
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main v0.2.0
```

#### Step 3: Monitor Release

1. Watch GitHub Actions: https://github.com/stephanschielke/open-webui-mcp-server/actions
2. Approve deployment when prompted
3. Verify PyPI upload: https://pypi.org/project/openwebui-mcp-server/

#### Step 4: Verify Installation

```bash
# Wait 5-10 minutes for PyPI CDN
pip install openwebui-mcp-server==0.2.0
openwebui-mcp --version
```

---

## Troubleshooting

### Issue: "OIDC token request failed"

**Cause**: Trusted publisher not configured

**Solution**:
1. Verify trusted publisher settings on PyPI
2. Ensure workflow name matches exactly
3. Ensure environment name matches

### Issue: "Version already exists"

**Cause**: Trying to publish existing version

**Solution**:
1. Bump version in `pyproject.toml`
2. Create new tag
3. Never reuse version numbers

### Issue: "Environment protection failed"

**Cause**: Deployment blocked

**Solution**:
1. Check if you're a required reviewer
2. Approve deployment in Actions UI
3. Verify deploying from `main` branch

---

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Semantic Versioning](https://semver.org/)
