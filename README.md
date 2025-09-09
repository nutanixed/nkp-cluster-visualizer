# NKP Cluster Visualizer

A Kubernetes cluster visualization dashboard for Nutanix Kubernetes Platform (NKP).

## Features

- Real-time cluster overview with node and pod information
- Worker pool visualization
- Deployment and service monitoring
- Architecture-style dashboard with modern UI
- Auto-refresh capabilities

## Environment Variables

- `BIND_PORT`: Port to bind the application (default: 9090)
- `CLUSTER_NAME`: Name of the cluster (default: nkp-dev01)
- `REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 30)

## Running Locally

```bash
pip install -r requirements.txt
python3 cluster_api.py
```

## Docker Build

```bash
docker build -t nkp-cluster-visualizer .
docker run -p 9090:9090 nkp-cluster-visualizer
```

## Kubernetes Deployment

See the `k8s/` directory for Kubernetes manifests.