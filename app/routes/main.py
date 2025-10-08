"""
Main routes - Dashboard pages and API endpoints
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from app.utils import login_required
from cluster_api import get_cluster_data, v1, apps_v1
from kubernetes import client

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('index.html')


@main_bp.route('/api/cluster')
@login_required
def cluster_api():
    """Get cluster data"""
    return jsonify(get_cluster_data())


@main_bp.route('/api/health')
def health_check():
    """Health check endpoint for Kubernetes probes"""
    try:
        # Simple health check - try to connect to Kubernetes API
        v1.list_node(limit=1)
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'version': '2.1.0'
        }), 500


@main_bp.route('/api/refresh', methods=['POST'])
@login_required
def refresh_data():
    """Force refresh cluster data"""
    try:
        data = get_cluster_data()
        return jsonify({
            'status': 'success',
            'message': 'Data refreshed successfully',
            'timestamp': data.get('last_updated'),
            'nodes': data.get('total_nodes', 0),
            'pods': data.get('total_pods', 0)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to refresh data: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@main_bp.route('/api/deployments/<namespace>/<deployment_name>/scale', methods=['POST'])
@login_required
def scale_deployment(namespace, deployment_name):
    """Scale a deployment or statefulset to the specified number of replicas"""
    try:
        data = request.get_json()
        if not data or 'replicas' not in data:
            return jsonify({'error': 'Missing replicas parameter'}), 400
        
        replicas = int(data['replicas'])
        if replicas < 0:
            return jsonify({'error': 'Replicas must be non-negative'}), 400
        
        # Try to find as a deployment first
        resource_type = 'Deployment'
        try:
            deployment = apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            # Update the replica count
            deployment.spec.replicas = replicas
            
            # Apply the update
            apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
                body=deployment
            )
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # Not a deployment, try as a statefulset
                resource_type = 'StatefulSet'
                try:
                    statefulset = apps_v1.read_namespaced_stateful_set(
                        name=deployment_name,
                        namespace=namespace
                    )
                    # Update the replica count
                    statefulset.spec.replicas = replicas
                    
                    # Apply the update
                    apps_v1.patch_namespaced_stateful_set(
                        name=deployment_name,
                        namespace=namespace,
                        body=statefulset
                    )
                except client.exceptions.ApiException as e2:
                    if e2.status == 404:
                        return jsonify({'error': f'Deployment or StatefulSet {deployment_name} not found in namespace {namespace}'}), 404
                    raise
            else:
                raise
        
        print(f"Successfully scaled {resource_type} {namespace}/{deployment_name} to {replicas} replicas")
        
        return jsonify({
            'success': True,
            'message': f'{resource_type} {deployment_name} scaled to {replicas} replicas',
            'deployment': deployment_name,
            'namespace': namespace,
            'replicas': replicas,
            'type': resource_type
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid replicas value - must be a number'}), 400
    except Exception as e:
        print(f"Error scaling {namespace}/{deployment_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to scale: {str(e)}'}), 500


@main_bp.route('/api/deployments/<namespace>/<deployment_name>/replicas', methods=['GET'])
@login_required
def get_deployment_replicas(namespace, deployment_name):
    """Get current replica information for a deployment or statefulset"""
    try:
        # Try to find as a deployment first
        resource_type = 'Deployment'
        try:
            deployment = apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace
            )
            
            return jsonify({
                'deployment': deployment_name,
                'namespace': namespace,
                'type': resource_type,
                'desired_replicas': deployment.spec.replicas or 0,
                'ready_replicas': deployment.status.ready_replicas or 0,
                'available_replicas': deployment.status.available_replicas or 0,
                'updated_replicas': deployment.status.updated_replicas or 0,
                'unavailable_replicas': deployment.status.unavailable_replicas or 0
            })
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # Not a deployment, try as a statefulset
                resource_type = 'StatefulSet'
                statefulset = apps_v1.read_namespaced_stateful_set(
                    name=deployment_name,
                    namespace=namespace
                )
                
                return jsonify({
                    'deployment': deployment_name,
                    'namespace': namespace,
                    'type': resource_type,
                    'desired_replicas': statefulset.spec.replicas or 0,
                    'ready_replicas': statefulset.status.ready_replicas or 0,
                    'available_replicas': statefulset.status.ready_replicas or 0,  # StatefulSets don't have available_replicas
                    'updated_replicas': statefulset.status.updated_replicas or 0,
                    'current_replicas': statefulset.status.current_replicas or 0
                })
            else:
                raise
        
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return jsonify({'error': f'Deployment or StatefulSet {deployment_name} not found in namespace {namespace}'}), 404
        return jsonify({'error': f'Failed to get resource info: {str(e)}'}), 500
    except Exception as e:
        print(f"Error getting resource info {namespace}/{deployment_name}: {e}")
        return jsonify({'error': f'Failed to get resource info: {str(e)}'}), 500