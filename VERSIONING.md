# Versioning Strategy

## Overview
This project follows **Semantic Versioning 2.0.0** (https://semver.org/) with a tag-based release strategy.

## Version Format
```
vMAJOR.MINOR.PATCH
```

### Version Increment Rules:
- **MAJOR** (v3.0.0): Breaking changes, incompatible API changes
- **MINOR** (v2.1.0): New features, backward-compatible functionality
- **PATCH** (v2.0.1): Bug fixes, backward-compatible fixes

## Branching Strategy

### Main Branch
- **Purpose**: Production-ready code
- **Protection**: All changes should be tested before merging
- **Deployment**: Production deployments reference specific version tags

### Feature Development
```
main ← feature/feature-name
```
- Create feature branches from main
- Merge back to main when ready
- Tag releases on main

## Release Process

### 1. Development
```bash
# Create feature branch
git checkout -b feature/statefulset-support

# Make changes and commit
git add .
git commit -m "Add StatefulSet support"

# Push to remote
git push origin feature/statefulset-support
```

### 2. Merge to Main
```bash
# Switch to main and merge
git checkout main
git merge feature/statefulset-support
git push origin main
```

### 3. Create Release Tag
```bash
# Create annotated tag with release notes
git tag -a v2.1.0 -m "Release v2.1.0: Add StatefulSet support

Features:
- Added StatefulSet querying alongside Deployments
- StatefulSets now visible in Application Deployments view
- Updated scaling API to support both resource types"

# Push tag to remote
git push origin v2.1.0
```

### 4. Update Deployment
```bash
# Update ConfigMap to reference new version
kubectl patch configmap nkp-cluster-visualizer-config-v2 -n default \
  --type merge -p '{"data":{"VERSION":"v2.1.0"}}'

# Update ConfigMap labels
kubectl patch configmap nkp-cluster-visualizer-config-v2 -n default \
  --type merge -p '{"metadata":{"labels":{"version":"v2.1.0"}}}'

# Restart deployment to pull new version
kubectl rollout restart deployment nkp-cluster-visualizer-v2 -n default

# Monitor rollout
kubectl rollout status deployment nkp-cluster-visualizer-v2 -n default
```

## Version History

### v2.1.0 (2025-10-05)
**Features:**
- Added StatefulSet support to visualizer
- StatefulSets now visible in Application Deployments view
- Added visual indicators (⚙️ gear icon) for StatefulSets in UI
- Updated scaling API to support both Deployments and StatefulSets
- Added type badges to distinguish resource types
- MySQL StatefulSets (prod-mysql01, prod-mysql02) now visible

### v2.0.0 (Previous Release)
**Features:**
- Initial v2 release with enhanced UI
- Application view with deployment details
- Node topology visualization
- Service discovery
- Real-time cluster metrics

### v1.0.0 (Initial Release)
**Features:**
- Basic cluster visualization
- Node and pod listing
- Simple deployment view

## Rollback Procedure

If issues are discovered after deployment:

```bash
# Rollback to previous version
kubectl patch configmap nkp-cluster-visualizer-config-v2 -n default \
  --type merge -p '{"data":{"VERSION":"v2.0.0"}}'

kubectl rollout restart deployment nkp-cluster-visualizer-v2 -n default
```

## Best Practices

1. **Always tag releases**: Never deploy from untagged commits in production
2. **Test before tagging**: Ensure changes work in development/staging first
3. **Write descriptive release notes**: Include features, fixes, and breaking changes
4. **Update version in multiple places**:
   - Git tag
   - ConfigMap VERSION field
   - ConfigMap labels
   - Health check endpoint (cluster_api.py line 246)
5. **Keep CHANGELOG.md updated**: Document all changes for each version
6. **Use annotated tags**: Include release notes in tag message
7. **Never force-push tags**: Tags should be immutable once pushed

## Deployment Architecture

The visualizer uses an init container pattern:
```yaml
initContainers:
  - name: git-clone
    image: alpine/git
    command: ['sh', '-c', 'git clone -b $VERSION $GITHUB_REPO /app']
```

This clones the specific version tag at deployment time, ensuring:
- ✅ Reproducible deployments
- ✅ Easy version switching
- ✅ No container image rebuilds needed
- ✅ Fast rollbacks

## Version Verification

Check running version:
```bash
# Via API
curl http://10.142.152.207/api/health | jq .version

# Via ConfigMap
kubectl get configmap nkp-cluster-visualizer-config-v2 -n default -o jsonpath='{.data.VERSION}'

# Via pod logs
kubectl logs -n default -l app=nkp-cluster-visualizer --tail=20 | grep -i version
```

## Questions?

Contact: DevOps Team
Repository: https://github.com/nutanixed/nkp-cluster-visualizer