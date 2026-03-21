# Production Release Checklist

Use this checklist before every production release to ensure a smooth deployment.

## Pre-Release (Local)

### Code Quality
- [ ] All tests pass: `mise run owu:tests:all`
- [ ] Linter passes: `mise run owu:linter:check`
- [ ] No uncommitted changes: `git status`
- [ ] Branch is up to date: `git pull origin main`

### Version Management
- [ ] Version follows semantic versioning (MAJOR.MINOR.PATCH)
- [ ] CHANGELOG.md is updated (if using)
- [ ] Breaking changes are documented

### Documentation
- [ ] README.md reflects new features/changes
- [ ] API documentation is up to date
- [ ] Migration guide for breaking changes

### Dependencies
- [ ] `uv.lock` is up to date: `uv lock`
- [ ] No security vulnerabilities: `uv pip audit` (if available)

## Release Process

### Option 1: Automated (Recommended)
```bash
# Run all checks and create tag
mise run release:prepare X.Y.Z
```

### Option 2: Manual
```bash
# 1. Run checks
mise run owu:linter:check
mise run owu:tests:all

# 2. Bump version
mise run bump:patch  # or minor/major

# 3. Commit and tag
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main vX.Y.Z
```

## Post-Release Verification

### GitHub Actions
- [ ] Build job completed successfully
- [ ] Publish to Test PyPI succeeded
- [ ] Publish to PyPI succeeded (after approval)
- [ ] GitHub Release created

### PyPI
- [ ] Package appears on https://pypi.org/project/openwebui-mcp-server/
- [ ] Version number is correct
- [ ] Package metadata is correct

### Installation Test
```bash
# Wait 5-10 minutes for PyPI CDN
pip install openwebui-mcp-server==X.Y.Z
openwebui-mcp --version
```

### Documentation
- [ ] GitHub Release notes are accurate
- [ ] Installation instructions work
- [ ] No broken links in documentation

## Emergency Rollback

If a bad release is published:

1. **Yank the release** (preferred):
   ```bash
   pip install twine
   twine yank openwebui-mcp-server==X.Y.Z
   ```

2. **Publish hotfix**:
   ```bash
   # Fix the issue
   mise run bump:patch
   git add pyproject.toml
   git commit -m "fix: hotfix for vX.Y.Z"
   git tag -a vX.Y.(Z+1) -m "Hotfix release vX.Y.(Z+1)"
   git push origin main vX.Y.(Z+1)
   ```

3. **Notify users**:
   - Create GitHub issue explaining the problem
   - Update README with known issues
   - Post announcement if critical

## Notes

- Never reuse version numbers
- Always test installation after release
- Monitor GitHub Actions for any failures
- Keep rollback procedure ready
