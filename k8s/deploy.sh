#!/bin/bash

set -e

echo "=========================================="
echo "NKP Cluster Visualizer Deployment"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster"
    echo "Please ensure your kubeconfig is properly configured"
    exit 1
fi

echo "✓ Connected to Kubernetes cluster"
echo ""

# Apply manifests in order
echo "Applying Kubernetes manifests..."
echo ""

echo "1. Creating ServiceAccount..."
kubectl apply -f "${SCRIPT_DIR}/serviceaccount.yaml"

echo "2. Creating ClusterRole..."
kubectl apply -f "${SCRIPT_DIR}/clusterrole.yaml"

echo "3. Creating ClusterRoleBinding..."
kubectl apply -f "${SCRIPT_DIR}/clusterrolebinding.yaml"

echo "4. Creating ConfigMap..."
kubectl apply -f "${SCRIPT_DIR}/configmap.yaml"

echo "5. Creating Deployment..."
kubectl apply -f "${SCRIPT_DIR}/deployment.yaml"

echo "6. Creating Services..."
kubectl apply -f "${SCRIPT_DIR}/service.yaml"
kubectl apply -f "${SCRIPT_DIR}/loadbalancer.yaml"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Get service information
echo "Service Information:"
kubectl get svc -l app=nkp-cluster-visualizer

echo ""
echo "To access the application:"
echo "  1. Get the LoadBalancer IP:"
echo "     kubectl get svc nkp-cluster-visualizer-loadbalancer"
echo ""
echo "  2. Open in browser:"
echo "     http://<EXTERNAL-IP>"
echo ""
echo "To check deployment status:"
echo "  kubectl get pods -l app=nkp-cluster-visualizer"
echo ""
echo "To view logs:"
echo "  kubectl logs -l app=nkp-cluster-visualizer --tail=100"
echo ""
