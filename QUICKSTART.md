# NKP Cluster Visualizer - Quick Start

## 🚀 Deploy in 60 Seconds

### Prerequisites
- Kubernetes cluster with `kubectl` configured
- Cluster admin permissions
- LoadBalancer support (or use NodePort/port-forward)

### One-Command Deployment

```bash
kubectl apply -f https://raw.githubusercontent.com/nutanixed/nkp-cluster-visualizer/main/k8s/deployment-v2.yaml
```

### Access the Application

```bash
# Get the LoadBalancer IP
kubectl get svc nkp-cluster-visualizer-loadbalancer-v2

# Wait for EXTERNAL-IP to be assigned (may take 1-2 minutes)
# Then open in browser: http://<EXTERNAL-IP>
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -l app=nkp-cluster-visualizer

# Should show: Running and Ready (1/1)
```

### Alternative Access Methods

**If LoadBalancer is pending:**

```bash
# Use port-forward
kubectl port-forward svc/nkp-cluster-visualizer-service-v2 8080:80

# Access at: http://localhost:8080
```

## 🔧 Common Customizations

### Change Cluster Name

```bash
kubectl edit configmap nkp-cluster-visualizer-config-v2
# Change CLUSTER_NAME value
kubectl rollout restart deployment nkp-cluster-visualizer-v2
```

### Scale for High Availability

```bash
kubectl scale deployment nkp-cluster-visualizer-v2 --replicas=3
```

### Update to Latest Code

```bash
kubectl rollout restart deployment nkp-cluster-visualizer-v2
```

## 📚 Full Documentation

For detailed instructions, troubleshooting, and advanced configuration:
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[README.md](README.md)** - Application overview and features

## 🆘 Quick Troubleshooting

**Pod not starting?**
```bash
kubectl logs -l app=nkp-cluster-visualizer -c git-clone
kubectl logs -l app=nkp-cluster-visualizer -c nkp-cluster-visualizer
```

**LoadBalancer pending?**
```bash
# Use port-forward instead
kubectl port-forward svc/nkp-cluster-visualizer-service-v2 8080:80
```

**Permission errors?**
```bash
# Verify RBAC resources
kubectl get sa,clusterrole,clusterrolebinding -l app=nkp-cluster-visualizer
```

## 🗑️ Uninstall

```bash
kubectl delete -f https://raw.githubusercontent.com/nutanixed/nkp-cluster-visualizer/main/k8s/deployment-v2.yaml
```

---

**Need help?** See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive documentation.