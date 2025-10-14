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
# @login_required  # Temporarily disabled for testing
def index():
    """Main dashboard page"""
    return render_template('index.html')


@main_bp.route('/api/cluster')
# @login_required  # Temporarily disabled for testing
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
# @login_required  # Temporarily disabled for testing
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
# @login_required  # Temporarily disabled for testing
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


@main_bp.route('/resources')
# @login_required  # Temporarily disabled for testing
def resources():
    """Resources listing page"""
    return render_template('resources.html')


@main_bp.route('/api/resources')
# @login_required  # Temporarily disabled for testing
def resources_api():
    """Get all Kubernetes resources"""
    try:
        # Get all resource types
        pods = v1.list_pod_for_all_namespaces()
        deployments = apps_v1.list_deployment_for_all_namespaces()
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        replicasets = apps_v1.list_replica_set_for_all_namespaces()
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        pvs = v1.list_persistent_volume()
        configmaps = v1.list_config_map_for_all_namespaces()
        secrets = v1.list_secret_for_all_namespaces()
        services = v1.list_service_for_all_namespaces()
        service_accounts = v1.list_service_account_for_all_namespaces()
        
        # Get NDK custom resources
        custom_api = client.CustomObjectsApi()
        applications = []
        snapshots = []
        protection_plans = []
        
        try:
            apps_result = custom_api.list_cluster_custom_object(
                group='dataservices.nutanix.com',
                version='v1alpha1',
                plural='applications'
            )
            applications = apps_result.get('items', [])
        except:
            pass
        
        try:
            snapshots_result = custom_api.list_cluster_custom_object(
                group='dataservices.nutanix.com',
                version='v1alpha1',
                plural='applicationsnapshots'
            )
            snapshots = snapshots_result.get('items', [])
        except:
            pass
        
        try:
            plans_result = custom_api.list_cluster_custom_object(
                group='dataservices.nutanix.com',
                version='v1alpha1',
                plural='appprotectionplans'
            )
            protection_plans = plans_result.get('items', [])
        except:
            pass
        
        # Helper function to check if PVC is orphaned (not used by any pod)
        def is_pvc_orphaned(pvc_name, pvc_namespace):
            for pod in pods.items:
                if pod.metadata.namespace == pvc_namespace and pod.spec.volumes:
                    for volume in pod.spec.volumes:
                        if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name == pvc_name:
                            return False
            return True
        
        # Helper function to check if service is orphaned (no endpoints)
        def is_service_orphaned(svc_name, svc_namespace):
            try:
                endpoints = v1.read_namespaced_endpoints(name=svc_name, namespace=svc_namespace)
                if endpoints.subsets:
                    for subset in endpoints.subsets:
                        if subset.addresses:
                            return False
                return True
            except:
                return True
        
        # Helper function to check if configmap/secret is orphaned (not used by any pod)
        def is_config_orphaned(resource_name, resource_namespace, resource_type='configmap', resource_obj=None):
            # Check for special system resources that are not orphaned
            if resource_type == 'configmap':
                # kube-root-ca.crt is auto-created in every namespace for service account verification
                if resource_name == 'kube-root-ca.crt':
                    return False
            
            if resource_obj:
                # Check for ownerReferences - resources managed by CRDs/operators
                owner_refs = resource_obj.metadata.owner_references if resource_obj.metadata.owner_references else []
                if owner_refs:
                    # If it has an owner reference, it's managed by another resource
                    return False
                
                # Check for special labels that indicate operator/CRD usage
                labels = resource_obj.metadata.labels if resource_obj.metadata.labels else {}
                # Prometheus operator managed resources
                if 'managed-by' in labels and labels['managed-by'] == 'prometheus-operator':
                    return False
                # Alertmanager/Prometheus resources referenced by CRDs
                if 'alertmanager' in labels or 'prometheus' in labels:
                    return False
                
                # Check for app.kubernetes.io labels (Helm/operator managed applications)
                # These resources are part of an application deployment and used internally
                if 'app.kubernetes.io/name' in labels or 'app.kubernetes.io/instance' in labels:
                    return False
                
                # Kubernetes Dashboard resources - used internally by the dashboard app via API
                # The dashboard accesses these resources programmatically, not via volume mounts
                if resource_namespace == 'kubernetes-dashboard':
                    # Check both labeled and unlabeled dashboard resources
                    if resource_name in ['kubernetes-dashboard-settings', 'kubernetes-dashboard-csrf', 
                                        'kubernetes-dashboard-key-holder', 'kubernetes-dashboard-certs']:
                        # These are core dashboard resources used internally
                        return False
                    # Also check for labeled dashboard resources
                    if 'k8s-app' in labels and labels['k8s-app'] == 'kubernetes-dashboard':
                        return False
                
                if resource_type == 'secret':
                    # Check for special secret types used by operators/controllers
                    secret_type = resource_obj.type if hasattr(resource_obj, 'type') else None
                    if secret_type:
                        # NDK snapshot configuration secrets
                        if 'dataservices.nutanix.com' in secret_type:
                            return False
                        # Helm release secrets
                        if secret_type == 'helm.sh/release.v1':
                            return False
                        # Image pull secrets
                        if secret_type == 'kubernetes.io/dockerconfigjson':
                            # Check if used by any service account
                            try:
                                svc_accounts = v1.list_namespaced_service_account(resource_namespace)
                                for sa in svc_accounts.items:
                                    if sa.image_pull_secrets:
                                        for ips in sa.image_pull_secrets:
                                            if ips.name == resource_name:
                                                return False
                            except:
                                pass
                    
                    # Check for special annotations
                    annotations = resource_obj.metadata.annotations if resource_obj.metadata.annotations else {}
                    # cert-manager CA injection secrets
                    if 'cert-manager.io/allow-direct-injection' in annotations:
                        return False
                    
                    # Check for special finalizers that indicate operator usage
                    finalizers = resource_obj.metadata.finalizers if resource_obj.metadata.finalizers else []
                    for finalizer in finalizers:
                        # NDK snapshot protection
                        if 'dataservices.nutanix.com' in finalizer:
                            return False
            
            # Check if used by pods
            for pod in pods.items:
                if pod.metadata.namespace == resource_namespace:
                    # Check volumes
                    if pod.spec.volumes:
                        for volume in pod.spec.volumes:
                            if resource_type == 'configmap' and volume.config_map and volume.config_map.name == resource_name:
                                return False
                            if resource_type == 'secret' and volume.secret and volume.secret.secret_name == resource_name:
                                return False
                    # Check env vars in containers
                    if pod.spec.containers:
                        for container in pod.spec.containers:
                            # Check envFrom (entire configmap/secret as env vars)
                            if container.env_from:
                                for env_from in container.env_from:
                                    if resource_type == 'configmap' and env_from.config_map_ref and env_from.config_map_ref.name == resource_name:
                                        return False
                                    if resource_type == 'secret' and env_from.secret_ref and env_from.secret_ref.name == resource_name:
                                        return False
                            # Check individual env vars with valueFrom
                            if container.env:
                                for env_var in container.env:
                                    if env_var.value_from:
                                        if resource_type == 'configmap' and env_var.value_from.config_map_key_ref and env_var.value_from.config_map_key_ref.name == resource_name:
                                            return False
                                        if resource_type == 'secret' and env_var.value_from.secret_key_ref and env_var.value_from.secret_key_ref.name == resource_name:
                                            return False
                                    # Check plain env var values (e.g., CSI driver configmap names)
                                    elif env_var.value and env_var.value == resource_name:
                                        return False
                    # Check init containers as well
                    if pod.spec.init_containers:
                        for container in pod.spec.init_containers:
                            # Check envFrom
                            if container.env_from:
                                for env_from in container.env_from:
                                    if resource_type == 'configmap' and env_from.config_map_ref and env_from.config_map_ref.name == resource_name:
                                        return False
                                    if resource_type == 'secret' and env_from.secret_ref and env_from.secret_ref.name == resource_name:
                                        return False
                            # Check individual env vars with valueFrom
                            if container.env:
                                for env_var in container.env:
                                    if env_var.value_from:
                                        if resource_type == 'configmap' and env_var.value_from.config_map_key_ref and env_var.value_from.config_map_key_ref.name == resource_name:
                                            return False
                                        if resource_type == 'secret' and env_var.value_from.secret_key_ref and env_var.value_from.secret_key_ref.name == resource_name:
                                            return False
                                    # Check plain env var values
                                    elif env_var.value and env_var.value == resource_name:
                                        return False
            return True
        
        # Helper function to check if resource is pending deletion
        def is_pending_deletion(resource_obj):
            """Check if a resource has deletionTimestamp set (stuck in deletion)"""
            if hasattr(resource_obj, 'metadata') and hasattr(resource_obj.metadata, 'deletion_timestamp'):
                return resource_obj.metadata.deletion_timestamp is not None
            elif isinstance(resource_obj, dict):
                metadata = resource_obj.get('metadata', {})
                return metadata.get('deletionTimestamp') is not None
            return False
        
        # Format deployments
        deployment_list = []
        for dep in deployments.items:
            is_orphaned = (dep.spec.replicas or 0) == 0
            pending_deletion = is_pending_deletion(dep)
            deployment_list.append({
                'name': dep.metadata.name,
                'namespace': dep.metadata.namespace,
                'type': 'Deployment',
                'replicas': f"{dep.status.ready_replicas or 0}/{dep.spec.replicas or 0}",
                'age': dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else '',
                'labels': dep.metadata.labels or {},
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': dep.metadata.deletion_timestamp.isoformat() if pending_deletion and dep.metadata.deletion_timestamp else None,
                'finalizers': dep.metadata.finalizers if pending_deletion and dep.metadata.finalizers else []
            })
        
        # Format statefulsets
        statefulset_list = []
        for sts in statefulsets.items:
            is_orphaned = (sts.spec.replicas or 0) == 0
            pending_deletion = is_pending_deletion(sts)
            statefulset_list.append({
                'name': sts.metadata.name,
                'namespace': sts.metadata.namespace,
                'type': 'StatefulSet',
                'replicas': f"{sts.status.ready_replicas or 0}/{sts.spec.replicas or 0}",
                'age': sts.metadata.creation_timestamp.isoformat() if sts.metadata.creation_timestamp else '',
                'labels': sts.metadata.labels or {},
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': sts.metadata.deletion_timestamp.isoformat() if pending_deletion and sts.metadata.deletion_timestamp else None,
                'finalizers': sts.metadata.finalizers if pending_deletion and sts.metadata.finalizers else []
            })
        
        # Format PVCs
        pvc_list = []
        for pvc in pvcs.items:
            is_orphaned = is_pvc_orphaned(pvc.metadata.name, pvc.metadata.namespace)
            pending_deletion = is_pending_deletion(pvc)
            pvc_list.append({
                'name': pvc.metadata.name,
                'namespace': pvc.metadata.namespace,
                'status': pvc.status.phase,
                'volume': pvc.spec.volume_name or 'Pending',
                'capacity': pvc.status.capacity.get('storage', 'Unknown') if pvc.status.capacity else 'Pending',
                'storageClass': pvc.spec.storage_class_name or 'default',
                'age': pvc.metadata.creation_timestamp.isoformat() if pvc.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': pvc.metadata.deletion_timestamp.isoformat() if pending_deletion and pvc.metadata.deletion_timestamp else None,
                'finalizers': pvc.metadata.finalizers if pending_deletion and pvc.metadata.finalizers else []
            })
        
        # Format ConfigMaps
        configmap_list = []
        for cm in configmaps.items:
            # Skip system configmaps
            is_system = cm.metadata.namespace in ['kube-system', 'kube-public', 'kube-node-lease']
            is_orphaned = False if is_system else is_config_orphaned(cm.metadata.name, cm.metadata.namespace, 'configmap', cm)
            pending_deletion = is_pending_deletion(cm)
            configmap_list.append({
                'name': cm.metadata.name,
                'namespace': cm.metadata.namespace,
                'data_keys': len(cm.data.keys()) if cm.data else 0,
                'age': cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': cm.metadata.deletion_timestamp.isoformat() if pending_deletion and cm.metadata.deletion_timestamp else None,
                'finalizers': cm.metadata.finalizers if pending_deletion and cm.metadata.finalizers else []
            })
        
        # Format Secrets
        secret_list = []
        for secret in secrets.items:
            # Skip system secrets and service account tokens
            is_system = secret.metadata.namespace in ['kube-system', 'kube-public', 'kube-node-lease'] or secret.type == 'kubernetes.io/service-account-token'
            is_orphaned = False if is_system else is_config_orphaned(secret.metadata.name, secret.metadata.namespace, 'secret', secret)
            pending_deletion = is_pending_deletion(secret)
            secret_list.append({
                'name': secret.metadata.name,
                'namespace': secret.metadata.namespace,
                'type': secret.type,
                'data_keys': len(secret.data.keys()) if secret.data else 0,
                'age': secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': secret.metadata.deletion_timestamp.isoformat() if pending_deletion and secret.metadata.deletion_timestamp else None,
                'finalizers': secret.metadata.finalizers if pending_deletion and secret.metadata.finalizers else []
            })
        
        # Format Services
        service_list = []
        for svc in services.items:
            is_orphaned = is_service_orphaned(svc.metadata.name, svc.metadata.namespace)
            pending_deletion = is_pending_deletion(svc)
            service_list.append({
                'name': svc.metadata.name,
                'namespace': svc.metadata.namespace,
                'type': svc.spec.type,
                'clusterIP': svc.spec.cluster_ip,
                'externalIP': svc.status.load_balancer.ingress[0].ip if svc.status.load_balancer and svc.status.load_balancer.ingress else '-',
                'ports': ','.join([f"{p.port}/{p.protocol}" for p in svc.spec.ports]) if svc.spec.ports else '',
                'age': svc.metadata.creation_timestamp.isoformat() if svc.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': svc.metadata.deletion_timestamp.isoformat() if pending_deletion and svc.metadata.deletion_timestamp else None,
                'finalizers': svc.metadata.finalizers if pending_deletion and svc.metadata.finalizers else []
            })
        
        # Format Applications
        application_list = []
        for app in applications:
            metadata = app.get('metadata', {})
            status = app.get('status', {})
            conditions = status.get('conditions', [])
            state = 'Unknown'
            for condition in conditions:
                # NDK Applications use 'Active' condition type
                if condition.get('type') == 'Active':
                    state = 'Active' if condition.get('status') == 'True' else 'Inactive'
                    break
                # Fallback to 'Ready' for compatibility
                elif condition.get('type') == 'Ready':
                    state = 'Ready' if condition.get('status') == 'True' else 'NotReady'
                    break
            
            pending_deletion = is_pending_deletion(app)
            application_list.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'state': state,
                'age': metadata.get('creationTimestamp', ''),
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': metadata.get('deletionTimestamp'),
                'finalizers': metadata.get('finalizers', []) if pending_deletion else []
            })
        
        # Format Snapshots
        snapshot_list = []
        for snap in snapshots:
            metadata = snap.get('metadata', {})
            status = snap.get('status', {})
            
            # Determine state based on readyToUse field
            ready_to_use = status.get('readyToUse', False)
            if ready_to_use:
                state = 'Ready'
            elif 'readyToUse' in status:
                state = 'Not Ready'
            else:
                state = 'Unknown'
            
            pending_deletion = is_pending_deletion(snap)
            snapshot_list.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'state': state,
                'age': metadata.get('creationTimestamp', ''),
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': metadata.get('deletionTimestamp'),
                'finalizers': metadata.get('finalizers', []) if pending_deletion else []
            })
        
        # Format Protection Plans
        plan_list = []
        for plan in protection_plans:
            metadata = plan.get('metadata', {})
            spec = plan.get('spec', {})
            
            pending_deletion = is_pending_deletion(plan)
            plan_list.append({
                'name': metadata.get('name', ''),
                'namespace': metadata.get('namespace', ''),
                'application': spec.get('applicationName', ''),
                'age': metadata.get('creationTimestamp', ''),
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': metadata.get('deletionTimestamp'),
                'finalizers': metadata.get('finalizers', []) if pending_deletion else []
            })
        
        # Format Pods
        pod_list = []
        for pod in pods.items:
            # Determine pod status
            phase = pod.status.phase
            # Check for container statuses for more detailed status
            container_statuses = pod.status.container_statuses or []
            ready_containers = sum(1 for cs in container_statuses if cs.ready)
            total_containers = len(container_statuses)
            
            # Check if pod is orphaned (no owner references)
            is_orphaned = not pod.metadata.owner_references
            pending_deletion = is_pending_deletion(pod)
            
            # Extract owner information for grouping
            owner_name = None
            owner_kind = None
            if pod.metadata.owner_references:
                # Get the first owner (usually ReplicaSet for Deployments, or StatefulSet directly)
                owner = pod.metadata.owner_references[0]
                owner_name = owner.name
                owner_kind = owner.kind
            
            pod_list.append({
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'status': phase,
                'ready': f"{ready_containers}/{total_containers}",
                'restarts': sum(cs.restart_count for cs in container_statuses),
                'age': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else '',
                'node': pod.spec.node_name or 'Pending',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': pod.metadata.deletion_timestamp.isoformat() if pending_deletion and pod.metadata.deletion_timestamp else None,
                'finalizers': pod.metadata.finalizers if pending_deletion and pod.metadata.finalizers else [],
                'ownerName': owner_name,
                'ownerKind': owner_kind
            })
        
        # Format ReplicaSets
        replicaset_list = []
        for rs in replicasets.items:
            # Check if orphaned (no owner references, typically deployments)
            is_orphaned = not rs.metadata.owner_references
            pending_deletion = is_pending_deletion(rs)
            
            replicaset_list.append({
                'name': rs.metadata.name,
                'namespace': rs.metadata.namespace,
                'desired': rs.spec.replicas or 0,
                'current': rs.status.replicas or 0,
                'ready': rs.status.ready_replicas or 0,
                'age': rs.metadata.creation_timestamp.isoformat() if rs.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': rs.metadata.deletion_timestamp.isoformat() if pending_deletion and rs.metadata.deletion_timestamp else None,
                'finalizers': rs.metadata.finalizers if pending_deletion and rs.metadata.finalizers else []
            })
        
        # Format PersistentVolumes
        pv_list = []
        for pv in pvs.items:
            # Check if orphaned (not bound to any PVC)
            is_orphaned = pv.status.phase != 'Bound'
            pending_deletion = is_pending_deletion(pv)
            
            pv_list.append({
                'name': pv.metadata.name,
                'capacity': pv.spec.capacity.get('storage', 'Unknown') if pv.spec.capacity else 'Unknown',
                'accessModes': ','.join(pv.spec.access_modes) if pv.spec.access_modes else '',
                'reclaimPolicy': pv.spec.persistent_volume_reclaim_policy or 'Unknown',
                'status': pv.status.phase,
                'claim': pv.spec.claim_ref.name if pv.spec.claim_ref else '-',
                'claimNamespace': pv.spec.claim_ref.namespace if pv.spec.claim_ref else '-',
                'storageClass': pv.spec.storage_class_name or 'default',
                'age': pv.metadata.creation_timestamp.isoformat() if pv.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': pv.metadata.deletion_timestamp.isoformat() if pending_deletion and pv.metadata.deletion_timestamp else None,
                'finalizers': pv.metadata.finalizers if pending_deletion and pv.metadata.finalizers else []
            })
        
        # Format ServiceAccounts
        serviceaccount_list = []
        
        # Get all RoleBindings and ClusterRoleBindings to check for RBAC usage
        rbac_v1 = client.RbacAuthorizationV1Api()
        role_bindings = []
        cluster_role_bindings = []
        try:
            role_bindings = rbac_v1.list_role_binding_for_all_namespaces().items
            cluster_role_bindings = rbac_v1.list_cluster_role_binding().items
        except:
            pass
        
        for sa in service_accounts.items:
            # Skip system service accounts
            is_system = sa.metadata.namespace in ['kube-system', 'kube-public', 'kube-node-lease'] or sa.metadata.name == 'default'
            # Check if orphaned (not used by any pod or RBAC binding)
            is_orphaned = True
            if not is_system:
                # Check if used by any pod
                for pod in pods.items:
                    if pod.metadata.namespace == sa.metadata.namespace and pod.spec.service_account_name == sa.metadata.name:
                        is_orphaned = False
                        break
                
                # If not used by pods, check if used in RoleBindings or ClusterRoleBindings
                if is_orphaned:
                    # Check RoleBindings
                    for rb in role_bindings:
                        if rb.subjects:
                            for subject in rb.subjects:
                                if (subject.kind == 'ServiceAccount' and 
                                    subject.name == sa.metadata.name and 
                                    subject.namespace == sa.metadata.namespace):
                                    is_orphaned = False
                                    break
                        if not is_orphaned:
                            break
                    
                    # Check ClusterRoleBindings
                    if is_orphaned:
                        for crb in cluster_role_bindings:
                            if crb.subjects:
                                for subject in crb.subjects:
                                    if (subject.kind == 'ServiceAccount' and 
                                        subject.name == sa.metadata.name and 
                                        subject.namespace == sa.metadata.namespace):
                                        is_orphaned = False
                                        break
                            if not is_orphaned:
                                break
            else:
                is_orphaned = False
            
            pending_deletion = is_pending_deletion(sa)
            
            serviceaccount_list.append({
                'name': sa.metadata.name,
                'namespace': sa.metadata.namespace,
                'secrets': len(sa.secrets) if sa.secrets else 0,
                'age': sa.metadata.creation_timestamp.isoformat() if sa.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': sa.metadata.deletion_timestamp.isoformat() if pending_deletion and sa.metadata.deletion_timestamp else None,
                'finalizers': sa.metadata.finalizers if pending_deletion and sa.metadata.finalizers else []
            })
        
        return jsonify({
            'pods': pod_list,
            'deployments': deployment_list,
            'statefulsets': statefulset_list,
            'replicasets': replicaset_list,
            'services': service_list,
            'pvcs': pvc_list,
            'pvs': pv_list,
            'configmaps': configmap_list,
            'secrets': secret_list,
            'serviceaccounts': serviceaccount_list,
            'applications': application_list,
            'snapshots': snapshot_list,
            'protection_plans': plan_list,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error getting resources: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500