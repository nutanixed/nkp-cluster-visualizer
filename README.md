# NKP Cluster Visualizer v2.0.0

An enhanced Kubernetes cluster visualization tool with modern UI and improved functionality.

## 🚀 What's New in v2.0.0

### ✨ Enhanced UI & Design
- **Unified Color System**: Modern, consistent color palette with semantic meaning
- **Improved Visual Hierarchy**: Better contrast and readability
- **Interactive Elements**: Enhanced hover states and smooth animations
- **Responsive Design**: Better mobile and tablet support
- **Accessibility**: Focus states and improved keyboard navigation

### 🔧 Technical Improvements
- **Better Error Handling**: Graceful degradation when APIs are unavailable
- **Data Caching**: Improved performance with intelligent caching
- **Enhanced Logging**: Better debugging and monitoring capabilities
- **Health Checks**: Comprehensive health monitoring endpoints
- **Resource Usage**: Optional resource usage monitoring

### 🎨 Visual Enhancements
- **Brand Colors**: Indigo/Purple gradient for primary elements
- **Semantic Colors**: Green=success, Amber=warning, Red=error
- **Modern Shadows**: Subtle depth and elevation
- **Smooth Animations**: CSS transitions with modern easing
- **Component States**: Clear visual feedback for interactions

## 📋 Requirements

- Python 3.11+
- Kubernetes cluster access
- Flask and kubernetes Python libraries

## 🚀 Quick Start

### Local Development
```bash
pip install -r requirements.txt
python cluster_api.py
```

### Kubernetes Deployment
The application is designed to run in Kubernetes with proper RBAC permissions.

**📖 For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

Quick deploy from GitHub:
```bash
kubectl apply -f https://raw.githubusercontent.com/nutanixed/nkp-cluster-visualizer/main/k8s/deployment-v2.yaml
```

## 🔧 Configuration

Environment variables:
- `BIND_PORT`: Server port (default: 9090)
- `CLUSTER_NAME`: Display name for the cluster
- `REFRESH_INTERVAL`: Data refresh interval in seconds
- `ENABLE_DRILL_DOWN`: Enable detailed component views
- `SHOW_RESOURCE_USAGE`: Show resource usage metrics
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `THEME`: UI theme (nutanix, default)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │────│  Flask Server   │────│ Kubernetes API  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │  Data Collector │
                       └─────────────────┘
```

## 🔍 API Endpoints

- `GET /` - Main dashboard
- `GET /api/cluster` - Cluster data JSON
- `GET /api/health` - Health check
- `GET /api/refresh` - Force data refresh

## 🎯 Features

### Dashboard Views
- **Cluster Overview**: High-level cluster status
- **Node Details**: Comprehensive node information
- **Deployment Management**: Application deployment status
- **Service Discovery**: Service and networking overview
- **Pod Monitoring**: Real-time pod status and logs

### Interactive Elements
- **Version Selection**: Switch between v1.0 and v2.0
- **Real-time Updates**: Auto-refresh with configurable intervals
- **Drill-down Views**: Detailed component inspection
- **Quick Actions**: Scale deployments, restart pods
- **Search & Filter**: Find resources quickly

## 🔒 Security

- RBAC-compliant with minimal required permissions
- No persistent data storage
- Read-only cluster access
- Secure in-cluster communication

## 📊 Monitoring

- Health check endpoint for monitoring systems
- Structured logging for observability
- Performance metrics and caching
- Error tracking and alerting

## 🤝 Contributing

This is v2.0.0 of the NKP Cluster Visualizer. For issues or feature requests, please contact the development team.

## 📄 License

Internal Nutanix tool - All rights reserved.