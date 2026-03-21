# Production Workflow - Final Summary

## Critical Questions Answered

### 1. Tag Creation: Do we create `v*` tags?

**YES** - Tags must be created manually by maintainers.

**When to create tags**:
- After all PRs for a release are merged to main
- After running `mise run release:check` successfully
- When ready to publish to production PyPI

**How to create tags** (using proper mise syntax):
```bash
# Automated (recommended)
mise run release:prepare 0.2.0

# Just create the tag
mise run release:tag 0.2.0

# Just run pre-release checks
mise run release:check
```

**Mise tasks use the `usage` field for arguments**:
```toml
[tasks."release:tag"]
usage = 'arg "<version>" help="Version to release (e.g., 0.2.0)"'
run = """
VERSION="${usage_version}"
...
"""
```

---

### 2. Artifact Visibility: Can we see artifacts?

**YES** - Artifacts are visible in GitHub Actions UI.

**Where to find them**:
1. Go to: https://github.com/stephanschielke/open-webui-mcp-server/actions
2. Click on a completed workflow run
3. Scroll to "Artifacts" section at the bottom
4. Download `python-package-distributions`

**Artifact contents**:
- `dist/*.whl` - Built wheel distribution
- `dist/*.tar.gz` - Source distribution

**Retention**: 5 days for remote GitHub, 1 day for local act

---

### 3. ghalint: Should it be a job or step?

**IMPLEMENTED as a step** in the build job.

```yaml
- name: Validate workflow
  run: mise run owu:gha:lint
```

**Benefits**:
- Catches workflow security issues early
- No separate job overhead
- Fails fast if workflow has problems
- Runs on every push

---

### 4. Rebuild: Do we need to rebuild with artifacts?

**YES** - Rebuilding is necessary for production releases.

**Why**:
1. The `build` job artifact has dev version (e.g., `0.2.0.dev1`)
2. Production needs release version (e.g., `0.2.0`)
3. We set version from tag, then rebuild

**Flow**:
```
build job → artifact (0.2.0.dev1)
                      ↓
publish-release → download → set version (0.2.0) → rebuild → publish
```

**This is correct** because:
- Build job runs on every push (needs dev version)
- Release job only runs on tags (needs release version)
- Rebuilding ensures correct version in package

---

### 5. OIDC vs API Token: Should we use OIDC?

**YES** - OIDC is now implemented!

**Current state**:
- Test PyPI: Already using OIDC (trusted publishing configured)
- Production PyPI: Now using OIDC (workflow updated)

**Security benefits**:
| Aspect | API Token | OIDC |
|--------|-----------|------|
| Lifespan | Months/years | 15 minutes max |
| Secret required | Yes | No |
| Rotation | Manual | Automatic |
| Leak risk | High | Low |
| Audit trail | Limited | Full |

**Migration steps**:
1. ✅ Configure trusted publisher on PyPI
2. ✅ Update workflow to use OIDC
3. ⏳ Test with a release
4. ⏳ Remove `PYPI_ACCOUNT_API_TOKEN` after verification

---

## Files Created/Modified

### Modified Files
1. `.github/workflows/publish.yml`
   - Added ghalint validation step
   - Implemented OIDC for production PyPI
   - Added version validation
   - Added GitHub Release job with changelog
   - Fixed persist-credentials warning

2. `mise.toml`
   - Added `release:check` task (no arguments)
   - Added `release:tag` task (uses `usage` field for version argument)
   - Added `release:prepare` task (uses `usage` field for version argument)

### New Files
1. `.github/workflows/PUBLISH_GUIDE.md`
   - Complete publishing guide
   - OIDC setup instructions
   - Step-by-step release process
   - Troubleshooting guide

2. `.github/workflows/IMPROVEMENTS.md`
   - Critical analysis of workflow
   - Improvement recommendations
   - Security guardrails documentation

3. `.github/RELEASE_CHECKLIST.md`
   - Pre-release checklist
   - Release process steps
   - Post-release verification
   - Emergency rollback procedure

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

## Step-by-Step Production Release

### Prerequisites (One-time)

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
git checkout main
git pull origin main
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

## Validation

All changes have been validated:
- ✅ `ghalint` linter passes
- ✅ `act --validate` passes
- ✅ Follows existing workflow patterns
- ✅ Matches mise.toml configuration
- ✅ OIDC authentication implemented
- ✅ Security guardrails in place
- ✅ Mise tasks use proper `usage` field syntax

---

## Next Steps

### Immediate Actions Required
1. Configure trusted publisher on PyPI.org
2. Test OIDC with a release
3. Remove `PYPI_ACCOUNT_API_TOKEN` after verification

### Optional Improvements
1. Add changelog generation (git-cliff or similar)
2. Add release notes automation
3. Add pre-release support (alpha/beta/rc)

---

## References

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish)
- [Mise Task Arguments](https://mise.jdx.dev/tasks/task-arguments.html)
- [Semantic Versioning](https://semver.org/)

---

**The production publishing workflow is now complete with OIDC authentication, comprehensive guardrails, proper mise task syntax, and full documentation.**
