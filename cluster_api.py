#!/usr/bin/env python3
"""
NKP Cluster Visualizer v2.0.0
Enhanced version with improved UI, better error handling, and modern design
"""

import os
import json
import time
import logging
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
BIND_PORT = int(os.getenv('BIND_PORT', 9090))
REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', 30))
CLUSTER_NAME = os.getenv('CLUSTER_NAME', 'NKP Cluster')
ENABLE_DRILL_DOWN = os.getenv('ENABLE_DRILL_DOWN', 'true').lower() == 'true'
SHOW_RESOURCE_USAGE = os.getenv('SHOW_RESOURCE_USAGE', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
THEME = os.getenv('THEME', 'nutanix')

# Set log level
logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

# Initialize Kubernetes client
try:
    # Try in-cluster config first
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes configuration")
except:
    try:
        # Fall back to local kubeconfig
        config.load_kube_config()
        logger.info("Loaded local Kubernetes configuration")
    except Exception as e:
        logger.error(f"Failed to load Kubernetes configuration: {e}")
        raise

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

class ClusterDataCollector:
    """Enhanced data collector with better error handling and caching"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 30  # seconds
        self.last_update = 0
    
    def get_cluster_data(self, force_refresh=False):
        """Get comprehensive cluster data with caching"""
        current_time = time.time()
        
        if not force_refresh and (current_time - self.last_update) < self.cache_ttl and self.cache:
            logger.debug("Returning cached cluster data")
            return self.cache
        
        logger.info("Collecting fresh cluster data...")
        
        try:
            data = {
                'cluster_name': CLUSTER_NAME,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'nodes': self._get_nodes(),
                'namespaces': self._get_namespaces(),
                'deployments': self._get_deployments(),
                'services': self._get_services(),
                'pods': self._get_pods(),
                'system_info': self._get_system_info(),
                'resource_usage': self._get_resource_usage() if SHOW_RESOURCE_USAGE else None
            }
            
            self.cache = data
            self.last_update = current_time
            logger.info(f"Successfully collected data for {len(data['nodes'])} nodes, {len(data['deployments'])} deployments")
            
            return data
            
        except Exception as e:
            logger.error(f"Error collecting cluster data: {e}")
            # Return cached data if available, otherwise minimal data
            if self.cache:
                logger.warning("Returning cached data due to collection error")
                return self.cache
            else:
                return self._get_minimal_data()
    
    def _get_nodes(self):
        """Get node information with enhanced details"""
        try:
            nodes = v1.list_node()
            node_data = []
            
            for node in nodes.items:
                node_info = {
                    'name': node.metadata.name,
                    'status': 'Ready' if any(condition.type == 'Ready' and condition.status == 'True' 
                                           for condition in node.status.conditions) else 'NotReady',
                    'roles': self._get_node_roles(node),
                    'version': node.status.node_info.kubelet_version,
                    'os': f"{node.status.node_info.os_image}",
                    'kernel': node.status.node_info.kernel_version,
                    'container_runtime': node.status.node_info.container_runtime_version,
                    'addresses': [addr.address for addr in (node.status.addresses or [])],
                    'capacity': node.status.capacity,
                    'allocatable': node.status.allocatable,
                    'conditions': [{'type': c.type, 'status': c.status, 'reason': c.reason} 
                                 for c in (node.status.conditions or [])],
                    'created': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None
                }
                node_data.append(node_info)
            
            return node_data
            
        except ApiException as e:
            logger.error(f"Error fetching nodes: {e}")
            return []
    
    def _get_node_roles(self, node):
        """Determine node roles from labels"""
        labels = node.metadata.labels or {}
        roles = []
        
        if 'node-role.kubernetes.io/control-plane' in labels or 'node-role.kubernetes.io/master' in labels:
            roles.append('control-plane')
        if 'node-role.kubernetes.io/worker' in labels:
            roles.append('worker')
        if not roles:
            roles.append('worker')  # Default to worker if no specific role
            
        return roles
    
    def _get_namespaces(self):
        """Get namespace information"""
        try:
            namespaces = v1.list_namespace()
            return [
                {
                    'name': ns.metadata.name,
                    'status': ns.status.phase,
                    'created': ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
                    'labels': ns.metadata.labels or {}
                }
                for ns in namespaces.items
            ]
        except ApiException as e:
            logger.error(f"Error fetching namespaces: {e}")
            return []
    
    def _get_deployments(self):
        """Get deployment information across all namespaces"""
        try:
            deployments = apps_v1.list_deployment_for_all_namespaces()
            deployment_data = []
            
            for dep in deployments.items:
                deployment_info = {
                    'name': dep.metadata.name,
                    'namespace': dep.metadata.namespace,
                    'replicas': dep.spec.replicas,
                    'ready_replicas': dep.status.ready_replicas or 0,
                    'available_replicas': dep.status.available_replicas or 0,
                    'unavailable_replicas': dep.status.unavailable_replicas or 0,
                    'status': 'Ready' if (dep.status.ready_replicas or 0) == dep.spec.replicas else 'Pending',
                    'strategy': dep.spec.strategy.type if dep.spec.strategy else 'RollingUpdate',
                    'labels': dep.metadata.labels or {},
                    'selector': dep.spec.selector.match_labels or {},
                    'created': dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None,
                    'image': self._get_deployment_images(dep)
                }
                deployment_data.append(deployment_info)
            
            return deployment_data
            
        except ApiException as e:
            logger.error(f"Error fetching deployments: {e}")
            return []
    
    def _get_deployment_images(self, deployment):
        """Extract container images from deployment"""
        images = []
        if deployment.spec.template.spec.containers:
            for container in deployment.spec.template.spec.containers:
                images.append(container.image)
        return images
    
    def _get_services(self):
        """Get service information"""
        try:
            services = v1.list_service_for_all_namespaces()
            service_data = []
            
            for svc in services.items:
                service_info = {
                    'name': svc.metadata.name,
                    'namespace': svc.metadata.namespace,
                    'type': svc.spec.type,
                    'cluster_ip': svc.spec.cluster_ip,
                    'external_ips': svc.spec.external_i_ps or [],
                    'ports': [
                        {
                            'name': port.name,
                            'port': port.port,
                            'target_port': str(port.target_port),
                            'protocol': port.protocol
                        }
                        for port in (svc.spec.ports or [])
                    ],
                    'selector': svc.spec.selector or {},
                    'created': svc.metadata.creation_timestamp.isoformat() if svc.metadata.creation_timestamp else None
                }
                service_data.append(service_info)
            
            return service_data
            
        except ApiException as e:
            logger.error(f"Error fetching services: {e}")
            return []
    
    def _get_pods(self):
        """Get pod information with enhanced details"""
        try:
            pods = v1.list_pod_for_all_namespaces()
            pod_data = []
            
            for pod in pods.items:
                pod_info = {
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'status': pod.status.phase,
                    'node': pod.spec.node_name,
                    'ip': pod.status.pod_ip,
                    'host_ip': pod.status.host_ip,
                    'restart_count': sum(container.restart_count for container in (pod.status.container_statuses or [])),
                    'containers': self._get_container_info(pod),
                    'labels': pod.metadata.labels or {},
                    'created': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None,
                    'conditions': [
                        {'type': c.type, 'status': c.status, 'reason': c.reason}
                        for c in (pod.status.conditions or [])
                    ]
                }
                pod_data.append(pod_info)
            
            return pod_data
            
        except ApiException as e:
            logger.error(f"Error fetching pods: {e}")
            return []
    
    def _get_container_info(self, pod):
        """Get container information with proper status mapping"""
        containers = []
        spec_containers = pod.spec.containers or []
        status_containers = {cs.name: cs for cs in (pod.status.container_statuses or [])}
        
        for container in spec_containers:
            status = status_containers.get(container.name)
            container_info = {
                'name': container.name,
                'image': container.image,
                'ready': status.ready if status else False,
                'restart_count': status.restart_count if status else 0
            }
            containers.append(container_info)
        
        return containers
    
    def _get_system_info(self):
        """Get system-level information"""
        try:
            # Get cluster version info
            version_info = client.VersionApi().get_code()
            
            return {
                'kubernetes_version': f"{version_info.major}.{version_info.minor}",
                'git_version': version_info.git_version,
                'platform': version_info.platform,
                'build_date': version_info.build_date,
                'compiler': version_info.compiler,
                'visualizer_version': '2.0.0',
                'theme': THEME,
                'features': {
                    'drill_down': ENABLE_DRILL_DOWN,
                    'resource_usage': SHOW_RESOURCE_USAGE
                }
            }
        except Exception as e:
            logger.error(f"Error fetching system info: {e}")
            return {
                'kubernetes_version': 'Unknown',
                'visualizer_version': '2.0.0',
                'theme': THEME
            }
    
    def _get_resource_usage(self):
        """Get resource usage information (if metrics server is available)"""
        try:
            # This would require metrics server - placeholder for now
            return {
                'cpu_usage': 'Metrics server required',
                'memory_usage': 'Metrics server required',
                'storage_usage': 'Metrics server required'
            }
        except Exception as e:
            logger.error(f"Error fetching resource usage: {e}")
            return None
    
    def _get_minimal_data(self):
        """Return minimal data structure when collection fails"""
        return {
            'cluster_name': CLUSTER_NAME,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'nodes': [],
            'namespaces': [],
            'deployments': [],
            'services': [],
            'pods': [],
            'system_info': {'visualizer_version': '2.0.0', 'theme': THEME},
            'resource_usage': None,
            'error': 'Failed to collect cluster data'
        }

# Initialize data collector
collector = ClusterDataCollector()

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Read the HTML template
        with open('templates/index.html', 'r') as f:
            template = f.read()
        
        # Get cluster data
        cluster_data = collector.get_cluster_data()
        
        return render_template_string(template, 
                                    cluster_data=json.dumps(cluster_data),
                                    refresh_interval=REFRESH_INTERVAL * 1000)
    
    except FileNotFoundError:
        logger.error("Template file not found")
        return "Template file not found. Please ensure templates/index.html exists.", 500
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return f"Error loading dashboard: {str(e)}", 500

@app.route('/api/cluster')
def api_cluster():
    """API endpoint for cluster data"""
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        data = collector.get_cluster_data(force_refresh=force_refresh)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in API endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Simple health check - try to list namespaces
        v1.list_namespace(limit=1)
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/refresh')
def refresh_data():
    """Force refresh cluster data"""
    try:
        data = collector.get_cluster_data(force_refresh=True)
        return jsonify({
            'status': 'refreshed',
            'timestamp': data['timestamp'],
            'nodes': len(data['nodes']),
            'deployments': len(data['deployments'])
        })
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting NKP Cluster Visualizer v2.0.0")
    logger.info(f"Configuration:")
    logger.info(f"  - Bind Port: {BIND_PORT}")
    logger.info(f"  - Cluster Name: {CLUSTER_NAME}")
    logger.info(f"  - Refresh Interval: {REFRESH_INTERVAL}s")
    logger.info(f"  - Theme: {THEME}")
    logger.info(f"  - Drill Down: {ENABLE_DRILL_DOWN}")
    logger.info(f"  - Resource Usage: {SHOW_RESOURCE_USAGE}")
    
    app.run(host='0.0.0.0', port=BIND_PORT, debug=False)