# Kubernetes Manifests for NKP Cluster Visualizer

This directory contains all Kubernetes manifests required to deploy the NKP Cluster Visualizer.

## Files

- **serviceaccount.yaml** - ServiceAccount for the application
- **clusterrole.yaml** - ClusterRole with permissions for all resource types
- **clusterrolebinding.yaml** - Binds the ClusterRole to the ServiceAccount
- **configmap.yaml** - Configuration for the application
- **deployment.yaml** - Deployment specification
- **service.yaml** - ClusterIP Service
- **loadbalancer.yaml** - LoadBalancer Service for external access

## Deployment Instructions

### Quick Deploy

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or use the deploy script
./k8s/deploy.sh
```

### Manual Deploy (in order)

```bash
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/clusterrole.yaml
kubectl apply -f k8s/clusterrolebinding.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/loadbalancer.yaml
```

## Important: ClusterRole Permissions

**⚠️ CRITICAL**: When adding new Kubernetes resource types to the application, you **MUST** update the ClusterRole permissions in `clusterrole.yaml`.

### Current Supported Resources (v3.3.0)

The ClusterRole includes permissions for:

#### Core API (`""`)
- nodes, pods, services, namespaces
- persistentvolumeclaims, persistentvolumes
- configmaps, secrets, serviceaccounts
- endpoints, limitranges, resourcequotas

#### Apps API (`apps`)
- deployments, replicasets, daemonsets, statefulsets

#### Batch API (`batch`)
- cronjobs, jobs

#### Networking API (`networking.k8s.io`)
- ingresses, networkpolicies

#### Policy API (`policy`)
- poddisruptionbudgets

#### Autoscaling API (`autoscaling`)
- horizontalpodautoscalers

#### Storage API (`storage.k8s.io`)
- storageclasses

#### RBAC API (`rbac.authorization.k8s.io`)
- roles, rolebindings, clusterroles, clusterrolebindings

#### Snapshot API (`snapshot.storage.k8s.io`)
- volumesnapshots, volumesnapshotcontents, volumesnapshotclasses

#### Nutanix APIs
- `ndk.nutanix.com`: applications, applicationsnapshots, protectionplans, storageclusters, appprotectionplans
- `dataservices.nutanix.com`: applications, applicationsnapshots, protectionplans, appprotectionplans

### Adding New Resource Types

When you add support for new Kubernetes resource types in the code:

1. **Update `clusterrole.yaml`** - Add the new resource type to the appropriate API group
2. **Test locally** - Verify the application can access the new resources
3. **Update this README** - Document the new resource type
4. **Update CHANGELOG.md** - Document the change in the changelog
5. **Apply the updated ClusterRole**:
   ```bash
   kubectl apply -f k8s/clusterrole.yaml
   kubectl rollout restart deployment nkp-cluster-visualizer
   ```

### Example: Adding a New Resource Type

If you want to add support for `Ingress` resources:

```yaml
# Add to clusterrole.yaml under the appropriate apiGroup
- apiGroups:
  - networking.k8s.io
  resources:
  - ingresses  # <-- Add this
  verbs:
  - get
  - list
  - watch
```

## Configuration

Edit `configmap.yaml` to customize:

- `VERSION` - Git tag/branch to deploy (e.g., v3.3.0, main)
- `CLUSTER_NAME` - Display name for your cluster
- `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` - Login credentials
- `GITHUB_REPO` - Repository URL (if using a fork)

## Accessing the Application

After deployment:

```bash
# Get the LoadBalancer IP
kubectl get svc nkp-cluster-visualizer-loadbalancer

# Access via browser
http://<EXTERNAL-IP>
```

## Troubleshooting

### Permission Errors (403 Forbidden)

If you see 403 errors in the logs:

```bash
# Check pod logs
kubectl logs -l app=nkp-cluster-visualizer --tail=100 | grep 403

# The error will show which resource is forbidden
# Update clusterrole.yaml to add the missing permission
kubectl apply -f k8s/clusterrole.yaml
kubectl rollout restart deployment nkp-cluster-visualizer
```

### Health Check Failures

```bash
# Check pod status
kubectl get pods -l app=nkp-cluster-visualizer

# Check logs
kubectl logs -l app=nkp-cluster-visualizer --tail=50

# Verify health endpoint
kubectl exec -it <pod-name> -- curl http://localhost:9090/api/health
```

## Version History

- **v3.3.0** - Added 17 new resource types (CronJobs, Jobs, DaemonSets, Ingresses, NetworkPolicies, etc.)
- **v3.2.0** - Previous stable version
- **v3.0.0** - Initial production release
