# Changelog

All notable changes to the NKP Cluster Visualizer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-01-XX

### 🚨 Breaking Changes
- **Complete application restructure** - Migrated from monolithic structure to modular Flask application factory pattern
- **New authentication system** - Added login/logout functionality (breaking change for existing deployments)
- **Configuration management** - Introduced centralized config.py with environment variable support
- **Removed legacy files** - Dockerfile, DEPLOYMENT.md, QUICKSTART.md, README.md, VERSIONING.md, k8s/deployment-v2.yaml

### ✨ Added
- **Application Factory Pattern** - Implemented Flask application factory in `app/__init__.py`
- **Blueprint Architecture** - Separated routes into modular blueprints:
  - `app/routes/auth.py` - Authentication routes (login/logout)
  - `app/routes/main.py` - Dashboard and API routes
- **Configuration Management** - New `config.py` with support for:
  - Environment variables via python-dotenv
  - Configurable session timeout
  - Dashboard credentials management
  - Cluster name configuration
- **Authentication System**:
  - Login page with session management
  - `@login_required` decorator for protected routes
  - Configurable session timeout (default: 24 hours)
  - Logout functionality
- **Utility Modules** - Created `app/utils/` package:
  - `decorators.py` - Custom decorators including `@login_required`
- **Operational Scripts**:
  - `start-local.sh` - Production-ready startup script with pre-flight checks
  - `restart.sh` - Quick restart script for development
  - `backup.sh` - Backup utility for configuration and data
- **Enhanced Logging** - Structured logging to `flask.log`
- **Static Assets**:
  - `static/favicon.svg` - Custom favicon
  - `static/sk8s.jpg` - Branding image
- **New Dependencies**:
  - `python-dotenv==1.0.0` - Environment variable management
  - `pytz==2023.3` - Timezone support

### 🔄 Changed
- **Project Structure** - Reorganized from flat structure to modular architecture:
  ```
  Old:                          New:
  ├── app.py                    ├── run.py
  ├── cluster_api.py            ├── config.py
  ├── requirements.txt          ├── cluster_api.py
  └── templates/                ├── app/
      └── index.html            │   ├── __init__.py
                                │   ├── routes/
                                │   │   ├── auth.py
                                │   │   └── main.py
                                │   └── utils/
                                │       └── decorators.py
                                ├── templates/
                                │   ├── index.html
                                │   └── login.html
                                └── static/
  ```
- **Entry Point** - Renamed `app.py` to `run.py` with enhanced startup logging
- **cluster_api.py** - Enhanced error handling and logging
- **requirements.txt** - Updated and organized dependencies
- **templates/index.html** - Updated to work with new authentication system
- **Default Port** - Changed from 9090 to configurable via `BIND_PORT` environment variable

### 🔒 Security
- **Session Management** - Secure session handling with configurable timeouts
- **Authentication Required** - All dashboard routes now require authentication
- **Secret Key Management** - Configurable SECRET_KEY via environment variables
- **Credential Configuration** - Dashboard credentials configurable via environment variables

### 📝 Documentation
- **CHANGELOG.md** - Added comprehensive changelog (this file)
- **Inline Documentation** - Enhanced docstrings across all modules

### 🗑️ Removed
- `Dockerfile` - Removed legacy Docker configuration
- `DEPLOYMENT.md` - Removed outdated deployment documentation
- `QUICKSTART.md` - Removed outdated quick start guide
- `README.md` - Removed outdated readme (to be replaced)
- `VERSIONING.md` - Removed outdated versioning documentation
- `k8s/deployment-v2.yaml` - Removed legacy Kubernetes deployment manifest

### 🐛 Fixed
- Improved error handling in Kubernetes API calls
- Enhanced timezone handling with pytz
- Better session management and cleanup

### 🔧 Technical Details
- **Python Version**: 3.12+
- **Flask Version**: 2.3.3
- **Kubernetes Client**: 27.2.0
- **Architecture**: Blueprint-based modular design
- **Configuration**: Environment variable driven
- **Authentication**: Session-based with configurable timeout

### 📦 Migration Guide from v2.x to v3.0.0

#### For Developers:
1. **Update imports**: Routes are now in `app.routes` package
2. **Use application factory**: Import `create_app()` from `app` package
3. **Configuration**: Use `config.py` instead of hardcoded values
4. **Environment variables**: Create `.env` file for local development

#### For Operators:
1. **Set environment variables**:
   ```bash
   export SECRET_KEY="your-secret-key"
   export DASHBOARD_USERNAME="your-username"
   export DASHBOARD_PASSWORD="your-password"
   export CLUSTER_NAME="your-cluster-name"
   export BIND_PORT=5001
   ```
2. **Use new startup script**: `./start-local.sh` instead of direct Python execution
3. **Authentication required**: Configure credentials before deployment

---

## [2.1.0] - 2024-XX-XX

### Added
- Resource type toggle to filter between Deployments and StatefulSets
- StatefulSet support to visualizer
- Health check endpoint with version information

### Changed
- Updated health check to return v2.1.0

---

## [2.0.0] - 2024-XX-XX

### Added
- Major feature updates (details from previous releases)

---

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of NKP Cluster Visualizer
- Basic cluster visualization
- Node, Pod, Deployment, and Service views
- Real-time cluster data retrieval

---

## Version Comparison

| Version | Architecture | Authentication | Configuration | Deployment |
|---------|-------------|----------------|---------------|------------|
| v1.0.0  | Monolithic  | None           | Hardcoded     | Basic      |
| v2.0.0  | Monolithic  | None           | Hardcoded     | Enhanced   |
| v2.1.0  | Monolithic  | None           | Hardcoded     | Enhanced   |
| v3.0.0  | Modular     | Session-based  | Environment   | Production |

---

**Note**: This changelog was introduced in v3.0.0. Previous version details are summarized based on git history.