# NKP Cluster Visualizer

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/nutanixed/nkp-cluster-visualizer/releases/tag/v3.0.0)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-27.2.0-326CE5.svg)](https://kubernetes.io/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

A modern, production-ready web dashboard for visualizing Nutanix Kubernetes Platform (NKP) clusters. Built with Flask and the Kubernetes Python client, it provides real-time insights into cluster resources including nodes, pods, deployments, statefulsets, and services.

## 🌟 Features

### Core Functionality
- 📊 **Real-time Cluster Visualization** - Live view of cluster resources
- 🔄 **Resource Monitoring** - Track Nodes, Pods, Deployments, StatefulSets, and Services
- 🎯 **Resource Type Filtering** - Toggle between Deployments and StatefulSets
- 📈 **Resource Scaling** - Scale deployments directly from the dashboard
- 🔍 **Detailed Resource Views** - Comprehensive information for each resource type

### Architecture & Security
- 🏗️ **Modular Architecture** - Flask application factory pattern with blueprints
- 🔐 **Authentication System** - Session-based login with configurable credentials
- ⚙️ **Environment-Driven Configuration** - Flexible configuration via environment variables
- 🛡️ **Secure Session Management** - Configurable session timeouts
- 📝 **Comprehensive Logging** - Structured logging for debugging and monitoring

### Developer Experience
- 🚀 **Quick Start Scripts** - One-command startup with pre-flight checks
- 🔧 **Development Tools** - Restart and backup utilities included
- 📦 **Clean Project Structure** - Organized, maintainable codebase
- 🐍 **Modern Python** - Built with Python 3.12+ and latest best practices

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Prerequisites

### Required
- **Python 3.12+** - Modern Python runtime
- **Kubernetes Cluster** - NKP or any Kubernetes cluster
- **kubectl** - Kubernetes command-line tool (for startup validation)
- **kubeconfig** - Valid Kubernetes configuration (`~/.kube/config`)

### Optional
- **Virtual Environment** - Recommended for isolated dependencies
- **Git** - For version control and updates

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/nutanixed/nkp-cluster-visualizer.git
cd nkp-cluster-visualizer
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Kubernetes Access
```bash
kubectl cluster-info
kubectl get nodes
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development  # or production

# Dashboard Authentication
DASHBOARD_USERNAME=nutanix
DASHBOARD_PASSWORD=Nutanix/4u!

# Session Configuration
SESSION_TIMEOUT_HOURS=24

# Kubernetes Configuration
IN_CLUSTER=false  # Set to true when running inside Kubernetes
CLUSTER_NAME=nkp-dev01

# Application Configuration
BIND_PORT=5001
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask secret key for sessions |
| `FLASK_ENV` | `development` | Flask environment (development/production) |
| `DASHBOARD_USERNAME` | `nutanix` | Dashboard login username |
| `DASHBOARD_PASSWORD` | `Nutanix/4u!` | Dashboard login password |
| `SESSION_TIMEOUT_HOURS` | `24` | Session timeout in hours |
| `IN_CLUSTER` | `false` | Whether running inside Kubernetes |
| `CLUSTER_NAME` | `nkp-dev01` | Display name for the cluster |
| `BIND_PORT` | `9090` | Port to bind the application |

### Security Best Practices

⚠️ **Important**: Always change default credentials in production!

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Set strong credentials
export DASHBOARD_USERNAME="your-admin-user"
export DASHBOARD_PASSWORD="your-strong-password"
export SECRET_KEY="your-generated-secret-key"
```

## 🚀 Usage

### Quick Start (Recommended)

```bash
./start-local.sh
```

This script will:
1. ✅ Check for kubectl installation
2. ✅ Verify Kubernetes cluster connectivity
3. ✅ Activate virtual environment
4. ✅ Set environment variables
5. ✅ Start the application

### Manual Start

```bash
source .venv/bin/activate
export BIND_PORT=5001
python run.py
```

### Access the Dashboard

1. Open your browser to: `http://localhost:5001`
2. Login with configured credentials (default: `nutanix` / `Nutanix/4u!`)
3. View your cluster resources in real-time

### Restart the Application

```bash
./restart.sh
```

### Stop the Application

```bash
# Find the process
ps aux | grep "python.*run.py"

# Kill it
pkill -f "python.*nkp-cluster-visualizer.*run.py"
```

## 🏗️ Architecture

### Project Structure

```
nkp-cluster-visualizer/
├── app/                          # Application package
│   ├── __init__.py              # Application factory
│   ├── routes/                  # Route blueprints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   └── main.py             # Dashboard and API routes
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       └── decorators.py       # Custom decorators
├── static/                      # Static assets
│   ├── favicon.svg
│   └── sk8s.jpg
├── templates/                   # Jinja2 templates
│   ├── index.html              # Main dashboard
│   └── login.html              # Login page
├── cluster_api.py              # Kubernetes API client
├── config.py                   # Configuration management
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── start-local.sh             # Startup script
├── restart.sh                 # Restart script
├── backup.sh                  # Backup utility
├── CHANGELOG.md               # Version history
├── LICENSE                    # MIT License
└── README.md                  # This file
```

### Design Patterns

- **Application Factory** - Flask app created via factory function
- **Blueprint Architecture** - Modular route organization
- **Decorator Pattern** - `@login_required` for route protection
- **Configuration Object** - Centralized config management
- **Separation of Concerns** - Clear separation between routes, logic, and data

### Data Flow

```
User Browser
    ↓
Flask Routes (app/routes/)
    ↓
Authentication Check (@login_required)
    ↓
cluster_api.py (Kubernetes Client)
    ↓
Kubernetes API Server
    ↓
Cluster Resources (Nodes, Pods, etc.)
```

## 🔌 API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/login` | GET, POST | Login page | No |
| `/logout` | GET | Logout and clear session | No |

### Dashboard Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` | GET | Main dashboard page | Yes |
| `/api/cluster` | GET | Get cluster data (JSON) | Yes |
| `/api/health` | GET | Health check endpoint | No |
| `/api/refresh` | POST | Refresh cluster data | Yes |

### Resource Management Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/scale/<namespace>/<deployment>` | POST | Scale deployment | Yes |

### API Response Examples

#### Health Check
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000000",
  "version": "3.0.0"
}
```

#### Cluster Data
```json
{
  "nodes": [...],
  "pods": [...],
  "deployments": [...],
  "statefulsets": [...],
  "services": [...]
}
```

## 💻 Development

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/nutanixed/nkp-cluster-visualizer.git
cd nkp-cluster-visualizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set development environment
export FLASK_ENV=development
export BIND_PORT=5001

# Run in development mode
python run.py
```

### Development Tools

#### Hot Reload
Flask's development mode includes hot reload:
```bash
export FLASK_ENV=development
python run.py
```

#### Logging
Logs are written to `flask.log`:
```bash
tail -f flask.log
```

#### Backup Configuration
```bash
./backup.sh
```

### Code Style

- **PEP 8** - Follow Python style guidelines
- **Docstrings** - Document all functions and classes
- **Type Hints** - Use type hints where appropriate
- **Comments** - Explain complex logic

### Testing

```bash
# Test Kubernetes connectivity
kubectl cluster-info

# Test API endpoints
curl http://localhost:5001/api/health

# Test authentication
curl -X POST http://localhost:5001/login \
  -d "username=nutanix&password=Nutanix/4u!"
```

## 🚢 Deployment

### Local Development
```bash
./start-local.sh
```

### Production Deployment

#### 1. Set Production Environment Variables
```bash
export FLASK_ENV=production
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DASHBOARD_USERNAME="your-admin"
export DASHBOARD_PASSWORD="your-secure-password"
export BIND_PORT=5001
```

#### 2. Run with Production Server
```bash
# Using gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 "app:create_app()"

# Or using the startup script
./start-local.sh
```

### Kubernetes Deployment

All Kubernetes manifests are available in the `k8s/` directory.

#### Quick Deploy
```bash
# Deploy all resources
kubectl apply -f k8s/

# Or use the deployment script
./k8s/deploy.sh
```

#### Manual Deploy
```bash
# Apply manifests in order
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/clusterrole.yaml
kubectl apply -f k8s/clusterrolebinding.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/loadbalancer.yaml
```

#### Access the Application
```bash
# Get the LoadBalancer IP
kubectl get svc nkp-cluster-visualizer-loadbalancer

# Access via browser
http://<EXTERNAL-IP>
```

#### Important: ClusterRole Permissions

⚠️ **When adding new Kubernetes resource types**, you **MUST** update the ClusterRole in `k8s/clusterrole.yaml`.

See `k8s/README.md` for detailed instructions on managing permissions.

## 🔍 Troubleshooting

### Common Issues

#### 1. Cannot Connect to Kubernetes Cluster
```bash
# Check kubectl access
kubectl cluster-info

# Verify kubeconfig
echo $KUBECONFIG
cat ~/.kube/config

# Test API access
kubectl get nodes
```

#### 2. Authentication Fails
```bash
# Check environment variables
echo $DASHBOARD_USERNAME
echo $DASHBOARD_PASSWORD

# Verify .env file
cat .env

# Check session configuration
echo $SECRET_KEY
```

#### 3. Port Already in Use
```bash
# Find process using port
lsof -i :5001

# Kill the process
pkill -f "python.*nkp-cluster-visualizer.*run.py"

# Or use a different port
export BIND_PORT=5002
./start-local.sh
```

#### 4. Module Import Errors
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.12+
```

### Debug Mode

Enable detailed logging:
```bash
export FLASK_ENV=development
python run.py
```

Check logs:
```bash
tail -f flask.log
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Update CHANGELOG.md for notable changes
- Test thoroughly before submitting PR

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Nutanix** - For the Kubernetes Platform
- **Flask** - Web framework
- **Kubernetes Python Client** - API interaction
- **Community Contributors** - Thank you!

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/nutanixed/nkp-cluster-visualizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nutanixed/nkp-cluster-visualizer/discussions)

## 🗺️ Roadmap

### Planned Features
- [ ] Kubernetes deployment manifests
- [ ] Helm chart for easy deployment
- [ ] Multi-cluster support
- [ ] Advanced filtering and search
- [ ] Resource usage metrics
- [ ] Alert notifications
- [ ] Dark mode theme
- [ ] Export functionality (CSV, JSON)

---

**Made with ❤️ for the Kubernetes community**