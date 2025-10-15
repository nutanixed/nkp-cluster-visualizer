# Changelog

All notable changes to the NKP Cluster Visualizer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.4.0] - 2025-01-15

### 🐛 Fixed

#### NKD Resource Orphan Detection Logic
- **Removed Incorrect Orphan Detection**: Removed inappropriate orphan detection logic for NKD resources
  - **Applications**: No longer marked as orphaned (they are primary resources)
  - **ApplicationSnapshots**: No longer marked as orphaned (they are backups meant to persist)
  - **AppProtectionPlans**: No longer marked as orphaned (they are configuration resources)
  
#### ApplicationSnapshotRestore Improvements
- **Fixed State Detection**: ApplicationSnapshotRestores now correctly display their state
  - Changed from checking non-existent `Complete` condition to using `status.completed` field
  - Now properly checks `ApplicationRestoreFinalised` condition for successful completion
  - States now correctly show: "Successful", "Failed", "In Progress", or "Unknown" (previously all showed "Unknown")
- **Corrected Orphan Logic**: Restores are now marked as orphaned only when completed successfully
  - Orphaned restores represent historical data that can be safely cleaned up
  - Updated tooltip to "Restore completed successfully - historical data"
- **Fixed Field Reference**: Corrected snapshot reference from `spec.snapshotName` to `spec.applicationSnapshotName`
- **Fixed Expand/Collapse**: Added ApplicationSnapshotRestores to the toggleAllSections array so it properly expands/collapses
- **Fixed Orphaned Filter**: Added ApplicationSnapshotRestores to the toggleOrphanedFilter function so it properly expands/collapses when filtering

### 🔄 Changed

- **Backend Data Processing** (`app/routes/main.py`):
  - Simplified Applications orphan detection (lines 612-622) - Always returns `orphaned: False`
  - Simplified ApplicationSnapshots orphan detection (lines 639-649) - Always returns `orphaned: False`
  - Simplified AppProtectionPlans orphan detection (lines 657-667) - Always returns `orphaned: False`
  - Enhanced ApplicationSnapshotRestores state detection (lines 669-721) - Now uses proper status fields and conditions
  
- **Frontend Display** (`templates/resources.html`):
  - Removed orphaned styling and badges from Applications (line 2051)
  - Removed orphaned styling and badges from ApplicationSnapshots (line 2099)
  - Removed orphaned styling and badges from AppProtectionPlans (line 2122)
  - Updated ApplicationSnapshotRestores orphaned badge tooltip (line 2079)
  - Added ApplicationSnapshotRestores to toggleAllSections array (line 2625) - Fixes expand/collapse functionality
  - Added ApplicationSnapshotRestores to toggleOrphanedFilter arrays (lines 2662, 2680) - Fixes orphaned filter expand/collapse

### 📊 Impact

- **Accurate State Reporting**: ApplicationSnapshotRestores now show correct completion status
- **Reduced False Positives**: Eliminated incorrect orphan detection for NKD primary resources
- **Better Resource Management**: Only completed restores (historical data) are marked as orphaned
- **Clearer User Experience**: Orphaned badges now only appear where they make logical sense

### 🔧 Technical Details

- Modified `app/routes/main.py` - Fixed NKD resource orphan detection logic (lines 595-721)
- Modified `templates/resources.html` - Updated rendering functions for all four NKD resource types (lines 2040-2133)
- ApplicationSnapshotRestore state detection now properly handles:
  - `status.completed` boolean field
  - `ApplicationRestoreFinalised` condition for success
  - `Failed` condition for failures
  - `Progressing` condition for in-progress restores

---

## [3.3.0] - 2025-10-15

### ✨ New Features

#### Expanded Resource Coverage
- **30+ Kubernetes Resource Types**: Added comprehensive support for additional resource types
  - **ClusterRoles**: View cluster-wide roles with rule counts and orphan detection
  - **ClusterRoleBindings**: View cluster role bindings with subject information
  - **Roles**: View namespace-scoped roles with rule counts
  - **RoleBindings**: View role bindings with subject information
  - **CronJobs**: View scheduled jobs with schedule, suspend status, and last run time
  - **Jobs**: View batch jobs with completion status and failure counts
  - **DaemonSets**: View daemon sets with desired/current/ready pod counts
  - **Ingresses**: View ingress resources with class, hosts, and routing information
  - **NetworkPolicies**: View network policies with ingress/egress rule counts
  - **PodDisruptionBudgets**: View PDBs with min/max available settings
  - **HorizontalPodAutoscalers**: View HPAs with target resource, min/max replicas, and current metrics
  - **Endpoints**: View service endpoints with address and port information
  - **StorageClasses**: View storage classes with provisioner, reclaim policy, and binding mode
  - **LimitRanges**: View limit ranges with constraint counts
  - **ResourceQuotas**: View resource quotas with hard limit information
  - **VolumeSnapshotContents**: View volume snapshot contents with snapshot references
  - **VolumeSnapshots**: View volume snapshots with source PVC and ready status

#### Enhanced Orphan Detection
- **Advanced RBAC Orphan Detection**: Comprehensive orphan detection for RBAC resources
  - ClusterRoles checked against ClusterRoleBindings and RoleBindings
  - ClusterRoleBindings checked for empty subjects and non-existent role references
  - Roles checked against RoleBindings within their namespace
  - RoleBindings checked for empty subjects and non-existent role references
  - System resources (prefixed with `system:` or `cluster-`) automatically excluded from orphan detection

#### Improved UI/UX
- **Orphaned Resource Filter**: New toggle button to filter and view only orphaned resources
  - Automatically expands all sections when filtering by orphaned resources
  - Collapses all sections when switching back to all resources view
  - Makes it easy to identify and clean up unused resources
- **Enhanced Resource Display**: Better formatting for complex resource types
  - Subject information for role bindings (ServiceAccount, User, Group)
  - Schedule and status information for CronJobs
  - Completion and failure metrics for Jobs
  - Host and routing information for Ingresses
  - Metric information for HorizontalPodAutoscalers

### 🔄 Changed

- **Resource List Expansion**: Updated toggle functions to support all 30+ resource types
  - `toggleAllSections()` now handles complete resource list
  - `toggleOrphanedFilter()` expands/collapses all resource sections appropriately
- **Backend Data Processing**: Enhanced `get_orphaned_resources()` to collect and format all new resource types
  - Added comprehensive data collection for all Kubernetes API groups
  - Improved error handling for optional API resources
  - Better age formatting and metadata extraction

### 📊 Impact

- **Complete Cluster Visibility**: View virtually all Kubernetes resources in one place
- **Improved Resource Management**: Easier identification of orphaned resources across all types
- **Better Troubleshooting**: Comprehensive view helps identify configuration issues
- **Enhanced Cleanup**: Orphaned filter makes it easy to find and remove unused resources

### 🔧 Technical Details

- Modified `app/routes/main.py` - Added data collection for 17 new resource types
- Modified `templates/index.html` - Added render functions for all new resource types
- Modified `templates/resources.html` - Added tables and display logic for all new resource types
- Enhanced orphan detection logic for RBAC resources with cross-reference checking
- Added support for Kubernetes API groups: `batch/v1`, `networking.k8s.io/v1`, `policy/v1`, `autoscaling/v2`, `storage.k8s.io/v1`, `snapshot.storage.k8s.io/v1`

---

## [3.2.0] - 2025-01-09

### ✨ New Features

#### New Resources Page
- **Comprehensive Resource Viewer** (`templates/resources.html`): New dedicated page for viewing all Kubernetes resources
  - **Deployments**: View all deployments with expandable pod details showing replica counts and pod status
  - **StatefulSets**: View all statefulsets with expandable pod details
  - **Pods**: Shows orphaned and pending deletion pods (managed pods shown under their controllers)
  - **ReplicaSets**: View all replicasets with replica counts
  - **Services**: View all services with type, cluster IP, and port information
  - **PersistentVolumeClaims (PVCs)**: View PVCs with storage class, capacity, and bound volume details
  - **PersistentVolumes (PVs)**: View PVs with reclaim policy and binding status
  - **ConfigMaps**: View all configmaps with data key counts
  - **Secrets**: View all secrets with type and data key counts
  - **ServiceAccounts**: View all service accounts with secret counts
  - **Applications**: View Nutanix-specific application resources
  - **VolumeSnapshots**: View volume snapshots with source PVC and status
  - **Namespace Filtering**: Filter resources by namespace with multi-select dropdown
  - **Search Functionality**: Real-time search across all resource names
  - **Collapsible Sections**: Each resource type can be expanded/collapsed independently
  - **Hierarchical View**: Deployments and StatefulSets show their managed pods in expandable detail rows

#### Enhanced Orphan Detection
- **RBAC-Aware Service Account Detection**: Service accounts used in RoleBindings and ClusterRoleBindings are no longer incorrectly flagged as orphaned
  - Added RBAC API client initialization (`RbacAuthorizationV1Api`)
  - Check both namespace-scoped RoleBindings and cluster-scoped ClusterRoleBindings
  - Service accounts used for authentication/authorization purposes are now properly recognized
  - Prevents false positives for service accounts used in RBAC but not directly by pods

### 🐛 Fixed

- **UI Expansion Bug**: Fixed Deployments and StatefulSets not expanding when clicked in Resources page
  - Corrected DOM element ID references in `togglePodDetails()` function in `templates/resources.html`
  - Changed from `pod-details-${rowId}` to `${rowId}` pattern
  - Changed from `expand-icon-${rowId}` to `icon-${rowId}` pattern
  - Deployments and StatefulSets now properly expand/collapse to show pod details
- **Service Account False Positives**: Eliminated 3 false positive orphaned service accounts
  - `architecture-viewer` (default namespace) - Used by ClusterRoleBinding
  - `admin-user` (kubernetes-dashboard namespace) - Used by ClusterRoleBinding
  - `dashboard-admin-sa` (kubernetes-dashboard namespace) - Used by ClusterRoleBinding

### 🔄 Changed

- **Orphan Detection Logic** (`app/routes/main.py`): Enhanced service account orphan detection to check both usage patterns
  - Service accounts are checked against pod `spec.serviceAccountName` references
  - Service accounts are also checked as subjects in RoleBindings and ClusterRoleBindings
  - Comprehensive detection prevents false positives while maintaining accuracy
  - Added proper error handling for RBAC API calls

### 📊 Impact

- **Reduced False Positives**: Orphan detection now has 0 false positives (down from 3)
- **Improved Accuracy**: Service account detection now covers both usage patterns:
  - Pod identity (via `serviceAccountName` in pod specs)
  - RBAC subjects (via RoleBindings/ClusterRoleBindings for authentication/authorization)
- **Better UX**: Resources page now properly expands/collapses deployment and statefulset details
- **Cleaner Dashboard**: Orphaned resources view now only shows truly orphaned resources

### 🔧 Technical Details

- **New File**: `templates/resources.html` - Comprehensive resource viewer with 1,800+ lines of HTML, CSS, and JavaScript
- Modified `get_orphaned_resources()` function in `app/routes/main.py` (lines 682-736)
- Modified `togglePodDetails()` function in `templates/resources.html` (lines 1627-1640)
- Added RBAC API integration for comprehensive service account usage detection
- Added new route in `app/routes/main.py` to serve the resources page

---

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