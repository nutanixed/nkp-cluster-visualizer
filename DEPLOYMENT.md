# NKP Cluster Visualizer - Fresh Environment Deployment Guide

This guide walks you through deploying the NKP Cluster Visualizer from GitHub to a fresh Kubernetes environment.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Kubernetes Cluster Access**
   - `kubectl` installed and configured
   - Cluster admin permissions (for RBAC setup)
   - Kubernetes 1.19+ recommended

2. **Cluster Requirements**
   - LoadBalancer support (MetalLB, cloud provider LB, etc.)
   - Metrics Server (optional, for resource usage display)

3. **Network Access**
   - Outbound internet access from cluster (to pull images and clone GitHub repo)
   - GitHub repository accessible: `https://github.com/nutanixed/nkp-cluster-visualizer.git`

## 🚀 Deployment Steps

### Step 1: Verify Cluster Access

```bash
# Check cluster connectivity
kubectl cluster-info

# Verify you have admin permissions
kubectl auth can-i create clusterrole
# Should return "yes"

# Check current context
kubectl config current-context
```

### Step 2: Clone the Repository (Optional)

You can deploy directly from GitHub without cloning, but cloning helps you review and customize:

```bash
# Clone the repository
git clone https://github.com/nutanixed/nkp-cluster-visualizer.git
cd nkp-cluster-visualizer
```

### Step 3: Review and Customize Configuration

Edit `k8s/deployment-v2.yaml` to customize settings:

```yaml
# ConfigMap section (lines 13-21)
data:
  BIND_PORT: "9090"                    # Application port
  CLUSTER_NAME: "nkp-dev01"            # Change to your cluster name
  ENABLE_DRILL_DOWN: "true"            # Enable detailed views
  LOG_LEVEL: "INFO"                    # DEBUG, INFO, WARNING, ERROR
  REFRESH_INTERVAL: "30"               # Seconds between refreshes
  SHOW_RESOURCE_USAGE: "true"          # Show resource metrics
  THEME: "nutanix"                     # nutanix or default
  VERSION: "v2.0.0"                    # Git branch/tag to deploy
  GITHUB_REPO: "https://github.com/nutanixed/nkp-cluster-visualizer.git"
```

**Key Configuration Options:**

- **CLUSTER_NAME**: Display name shown in the UI
- **VERSION**: 
  - Use `v2.0.0` for stable release
  - Use `main` for latest development version
  - Use specific tag/branch for other versions
- **REFRESH_INTERVAL**: Lower = more real-time, higher = less API load
- **LOG_LEVEL**: Use `DEBUG` for troubleshooting, `INFO` for production

### Step 4: Deploy to Kubernetes

**Option A: Deploy from Local Clone**

```bash
# Apply the deployment
kubectl apply -f k8s/deployment-v2.yaml

# Verify deployment
kubectl get all -l app=nkp-cluster-visualizer
```

**Option B: Deploy Directly from GitHub**

```bash
# Deploy without cloning
kubectl apply -f https://raw.githubusercontent.com/nutanixed/nkp-cluster-visualizer/main/k8s/deployment-v2.yaml

# Verify deployment
kubectl get all -l app=nkp-cluster-visualizer
```

### Step 5: Monitor Deployment Progress

```bash
# Watch pod creation
kubectl get pods -l app=nkp-cluster-visualizer -w

# Check init container logs (git clone)
kubectl logs -l app=nkp-cluster-visualizer -c git-clone

# Check application logs
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer -f

# Check pod events
kubectl describe pod -l app=nkp-cluster-visualizer
```

**Expected Pod Lifecycle:**
1. **Init:0/1** - Git clone in progress
2. **PodInitializing** - Installing dependencies
3. **Running** - Application started
4. **Ready (1/1)** - Health checks passed

### Step 6: Access the Application

```bash
# Get LoadBalancer IP
kubectl get svc nkp-cluster-visualizer-loadbalancer-v2

# Example output:
# NAME                                      TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
# nkp-cluster-visualizer-loadbalancer-v2   LoadBalancer   10.96.123.45    10.142.152.207   80:30123/TCP
```

**Access Methods:**

1. **LoadBalancer (Recommended)**
   ```bash
   # Get the external IP
   EXTERNAL_IP=$(kubectl get svc nkp-cluster-visualizer-loadbalancer-v2 -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
   echo "Access at: http://${EXTERNAL_IP}"
   
   # Open in browser
   open http://${EXTERNAL_IP}  # macOS
   xdg-open http://${EXTERNAL_IP}  # Linux
   ```

2. **ClusterIP + Port Forward (Testing)**
   ```bash
   kubectl port-forward svc/nkp-cluster-visualizer-service-v2 8080:80
   # Access at: http://localhost:8080
   ```

3. **NodePort (Alternative)**
   ```bash
   # If LoadBalancer is not available, change service type to NodePort
   kubectl patch svc nkp-cluster-visualizer-loadbalancer-v2 -p '{"spec":{"type":"NodePort"}}'
   
   # Get NodePort
   NODE_PORT=$(kubectl get svc nkp-cluster-visualizer-loadbalancer-v2 -o jsonpath='{.spec.ports[0].nodePort}')
   NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
   echo "Access at: http://${NODE_IP}:${NODE_PORT}"
   ```

### Step 7: Verify Application Health

```bash
# Check health endpoint
EXTERNAL_IP=$(kubectl get svc nkp-cluster-visualizer-loadbalancer-v2 -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://${EXTERNAL_IP}/api/health

# Expected response:
# {"status":"healthy","version":"v2.0.0","timestamp":"..."}

# Check cluster data endpoint
curl http://${EXTERNAL_IP}/api/cluster | jq .
```

## 🔧 Post-Deployment Configuration

### Scale the Deployment

```bash
# Scale to 3 replicas for high availability
kubectl scale deployment nkp-cluster-visualizer-v2 --replicas=3

# Verify scaling
kubectl get pods -l app=nkp-cluster-visualizer
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap nkp-cluster-visualizer-config-v2

# Restart pods to apply changes
kubectl rollout restart deployment nkp-cluster-visualizer-v2

# Monitor rollout
kubectl rollout status deployment nkp-cluster-visualizer-v2
```

### Enable Metrics Server (Optional)

If you want resource usage display:

```bash
# Check if metrics-server is installed
kubectl get deployment metrics-server -n kube-system

# If not installed, install it
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify metrics are available
kubectl top nodes
kubectl top pods
```

## 🔍 Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -l app=nkp-cluster-visualizer

# Check events
kubectl describe pod -l app=nkp-cluster-visualizer

# Common issues:
# - ImagePullBackOff: Check internet connectivity
# - CrashLoopBackOff: Check application logs
# - Init:Error: Check git-clone init container logs
```

### Git Clone Fails

```bash
# Check init container logs
kubectl logs -l app=nkp-cluster-visualizer -c git-clone

# Common issues:
# - Network connectivity: Verify outbound internet access
# - GitHub rate limiting: Wait and retry
# - Invalid VERSION: Check ConfigMap VERSION value
```

### Application Crashes

```bash
# Check application logs
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer --tail=100

# Check for common issues:
# - Missing dependencies: Check requirements.txt installation
# - RBAC permissions: Verify ClusterRole and ClusterRoleBinding
# - Kubernetes API access: Check ServiceAccount configuration
```

### LoadBalancer Pending

```bash
# Check service status
kubectl get svc nkp-cluster-visualizer-loadbalancer-v2

# If EXTERNAL-IP shows <pending>:
# - Verify LoadBalancer controller is installed (MetalLB, etc.)
# - Check LoadBalancer controller logs
# - Use NodePort or port-forward as alternative
```

### RBAC Permission Errors

```bash
# Check ServiceAccount
kubectl get sa nkp-cluster-visualizer-sa-v2

# Check ClusterRole
kubectl get clusterrole nkp-cluster-visualizer-role-v2

# Check ClusterRoleBinding
kubectl get clusterrolebinding nkp-cluster-visualizer-binding-v2

# Verify permissions
kubectl auth can-i list pods --as=system:serviceaccount:default:nkp-cluster-visualizer-sa-v2
```

## 🔄 Updating the Application

### Update to Latest Code

```bash
# Method 1: Restart pods (pulls latest from GitHub)
kubectl rollout restart deployment nkp-cluster-visualizer-v2

# Method 2: Change VERSION in ConfigMap
kubectl edit configmap nkp-cluster-visualizer-config-v2
# Change VERSION to desired branch/tag
kubectl rollout restart deployment nkp-cluster-visualizer-v2
```

### Update Deployment Configuration

```bash
# Method 1: Edit in-place
kubectl edit deployment nkp-cluster-visualizer-v2

# Method 2: Apply updated YAML
kubectl apply -f k8s/deployment-v2.yaml

# Monitor rollout
kubectl rollout status deployment nkp-cluster-visualizer-v2
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment nkp-cluster-visualizer-v2

# Rollback to previous version
kubectl rollout undo deployment nkp-cluster-visualizer-v2

# Rollback to specific revision
kubectl rollout undo deployment nkp-cluster-visualizer-v2 --to-revision=2
```

## 🗑️ Uninstalling

```bash
# Delete all resources
kubectl delete -f k8s/deployment-v2.yaml

# Or delete by label
kubectl delete all,configmap,serviceaccount,clusterrole,clusterrolebinding -l app=nkp-cluster-visualizer

# Verify cleanup
kubectl get all -l app=nkp-cluster-visualizer
```

## 📊 Monitoring & Observability

### View Logs

```bash
# Real-time logs
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer -f

# Logs from all replicas
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer --all-containers=true

# Previous pod logs (after crash)
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer --previous
```

### Health Monitoring

```bash
# Check health endpoint
curl http://<EXTERNAL-IP>/api/health

# Check readiness
kubectl get pods -l app=nkp-cluster-visualizer -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}'

# Check resource usage
kubectl top pods -l app=nkp-cluster-visualizer
```

### Performance Tuning

```bash
# Adjust resource limits
kubectl set resources deployment nkp-cluster-visualizer-v2 \
  --limits=cpu=1000m,memory=1Gi \
  --requests=cpu=500m,memory=512Mi

# Adjust replicas for load
kubectl scale deployment nkp-cluster-visualizer-v2 --replicas=5
```

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Kubernetes Cluster                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              LoadBalancer Service                   │    │
│  │         (External IP: 10.142.152.207)              │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │              ClusterIP Service                      │    │
│  │              (Port 80 → 9090)                       │    │
│  └──────────────────────┬─────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │         Deployment (nkp-cluster-visualizer-v2)     │    │
│  │                                                      │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │ Pod 1                                       │   │    │
│  │  │  ┌──────────────────────────────────────┐ │   │    │
│  │  │  │ Init Container: alpine/git           │ │   │    │
│  │  │  │ - Clone from GitHub                  │ │   │    │
│  │  │  │ - Copy to /app volume                │ │   │    │
│  │  │  └──────────────────────────────────────┘ │   │    │
│  │  │  ┌──────────────────────────────────────┐ │   │    │
│  │  │  │ App Container: python:3.11-slim      │ │   │    │
│  │  │  │ - Install dependencies               │ │   │    │
│  │  │  │ - Run Flask app (cluster_api.py)     │ │   │    │
│  │  │  │ - Serve on port 9090                 │ │   │    │
│  │  │  └──────────────────────────────────────┘ │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  │  ... (additional replicas)                         │    │
│  └────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼─────────────────────────────┐    │
│  │              Kubernetes API Server                  │    │
│  │  (RBAC: ServiceAccount + ClusterRole)              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Considerations

### RBAC Permissions

The application requires these permissions:

- **Read-only**: nodes, pods, services, namespaces
- **Read/Write**: deployments (for scaling feature)
- **Metrics**: nodes, pods (optional, for resource usage)

### Network Security

- Application runs on port 9090 internally
- LoadBalancer exposes port 80 externally
- No persistent storage or sensitive data
- All communication within cluster uses ClusterIP

### Best Practices

1. **Use specific VERSION tags** instead of `main` for production
2. **Enable resource limits** to prevent resource exhaustion
3. **Monitor logs** for unauthorized access attempts
4. **Use NetworkPolicies** to restrict pod communication (optional)
5. **Regular updates** to pull security patches

## 📚 Additional Resources

- **GitHub Repository**: https://github.com/nutanixed/nkp-cluster-visualizer
- **Application README**: See README.md in repository
- **Kubernetes Documentation**: https://kubernetes.io/docs/

## 🆘 Support

For issues or questions:

1. Check application logs: `kubectl logs -l app=nkp-cluster-visualizer`
2. Review this troubleshooting guide
3. Check GitHub issues
4. Contact the development team

---

**Last Updated**: 2024
**Version**: v2.0.0
**Maintained by**: Nutanix Development Team