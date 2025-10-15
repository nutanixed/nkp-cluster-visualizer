# NKP Cluster Visualizer - Quick Start Guide

## Deploy to NKP in 30 Seconds

### Single Command Deployment (Recommended)

```bash
kubectl apply -f https://raw.githubusercontent.com/nutanixed/nkp-cluster-visualizer/v3.3.0/k8s/nkp-cluster-visualizer.yaml
```

Or if you have the repository cloned:

```bash
kubectl apply -f k8s/nkp-cluster-visualizer.yaml
```

### What Gets Deployed

- ✅ ServiceAccount with proper RBAC
- ✅ ClusterRole with 30+ resource permissions
- ✅ ClusterRoleBinding
- ✅ ConfigMap with application settings
- ✅ Deployment (3 replicas with health checks)
- ✅ ClusterIP Service
- ✅ LoadBalancer Service

### Access the Application

```bash
# Get the LoadBalancer IP
kubectl get svc nkp-cluster-visualizer-loadbalancer

# Wait for EXTERNAL-IP to be assigned
# Then open in browser: http://<EXTERNAL-IP>
```

### Default Credentials

- **Username**: `nutanix`
- **Password**: `Nutanix/4u!`

⚠️ **Change these in production!** Edit the ConfigMap before deploying.

### Verify Deployment

```bash
# Check pods are running
kubectl get pods -l app=nkp-cluster-visualizer

# Check services
kubectl get svc -l app=nkp-cluster-visualizer

# View logs
kubectl logs -l app=nkp-cluster-visualizer --tail=50
```

### Customize Configuration

Before deploying, edit `k8s/nkp-cluster-visualizer.yaml` and update the ConfigMap section:

```yaml
data:
  VERSION: "v3.3.0"
  CLUSTER_NAME: "your-cluster-name"        # Change this
  DASHBOARD_USERNAME: "your-username"       # Change this
  DASHBOARD_PASSWORD: "your-password"       # Change this
  SECRET_KEY: "your-secret-key"            # Change this
```

### Uninstall

```bash
kubectl delete -f k8s/nkp-cluster-visualizer.yaml
```

### Troubleshooting

**Pods not starting?**
```bash
kubectl describe pods -l app=nkp-cluster-visualizer
kubectl logs -l app=nkp-cluster-visualizer --tail=100
```

**Permission errors?**
- Check the ClusterRole has all required permissions
- See `k8s/README.md` for permission management

**Health checks failing?**
- Ensure `/api/health` endpoint is accessible
- Check pod logs for errors

### Next Steps

- Read the full documentation: `README.md`
- Learn about permission management: `k8s/README.md`
- Customize your deployment: `k8s/configmap.yaml`
