"""
Main routes - Dashboard pages and API endpoints
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from app.utils import login_required
from cluster_api import get_cluster_data, v1, apps_v1
from kubernetes import client

main_bp = Blueprint('main', __name__)
rbac_v1 = client.RbacAuthorizationV1Api()


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
        
        # Fetch ClusterRoleBindings and RoleBindings first
        cluster_role_bindings = []
        try:
            cluster_role_bindings = rbac_v1.list_cluster_role_binding().items
        except:
            pass
        
        role_bindings = []
        try:
            role_bindings = rbac_v1.list_role_binding_for_all_namespaces().items
        except:
            pass
        
        # Format ClusterRoles
        clusterrole_list = []
        cluster_roles = []
        try:
            cluster_roles = rbac_v1.list_cluster_role().items
        except:
            pass
        
        for cr in cluster_roles:
            # Check if orphaned (not referenced by any ClusterRoleBinding or RoleBinding)
            is_orphaned = True
            
            # Check ClusterRoleBindings
            for crb in cluster_role_bindings:
                if crb.role_ref and crb.role_ref.kind == 'ClusterRole' and crb.role_ref.name == cr.metadata.name:
                    is_orphaned = False
                    break
            
            # Check RoleBindings (can also reference ClusterRoles)
            if is_orphaned:
                for rb in role_bindings:
                    if rb.role_ref and rb.role_ref.kind == 'ClusterRole' and rb.role_ref.name == cr.metadata.name:
                        is_orphaned = False
                        break
            
            # System ClusterRoles are not orphaned
            is_system = cr.metadata.name.startswith('system:') or cr.metadata.name.startswith('cluster-')
            if is_system:
                is_orphaned = False
            
            pending_deletion = is_pending_deletion(cr)
            
            # Count rules
            rules_count = len(cr.rules) if cr.rules else 0
            
            clusterrole_list.append({
                'name': cr.metadata.name,
                'rules': rules_count,
                'age': cr.metadata.creation_timestamp.isoformat() if cr.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': cr.metadata.deletion_timestamp.isoformat() if pending_deletion and cr.metadata.deletion_timestamp else None,
                'finalizers': cr.metadata.finalizers if pending_deletion and cr.metadata.finalizers else []
            })
        
        # Format ClusterRoleBindings
        clusterrolebinding_list = []
        for crb in cluster_role_bindings:
            # Check if orphaned (no subjects or role doesn't exist)
            is_orphaned = not crb.subjects or len(crb.subjects) == 0
            
            # Check if the referenced ClusterRole exists
            if not is_orphaned and crb.role_ref:
                role_exists = any(cr.metadata.name == crb.role_ref.name for cr in cluster_roles)
                if not role_exists:
                    is_orphaned = True
            
            pending_deletion = is_pending_deletion(crb)
            
            # Get role name and subjects
            role_name = crb.role_ref.name if crb.role_ref else 'Unknown'
            subjects_count = len(crb.subjects) if crb.subjects else 0
            
            # Get first subject for display
            first_subject = ''
            if crb.subjects and len(crb.subjects) > 0:
                subj = crb.subjects[0]
                if subj.kind == 'ServiceAccount':
                    first_subject = f"{subj.kind}:{subj.namespace}/{subj.name}" if subj.namespace else f"{subj.kind}:{subj.name}"
                else:
                    first_subject = f"{subj.kind}:{subj.name}"
                if subjects_count > 1:
                    first_subject += f" (+{subjects_count - 1} more)"
            
            clusterrolebinding_list.append({
                'name': crb.metadata.name,
                'role': role_name,
                'subjects': first_subject,
                'subjectsCount': subjects_count,
                'age': crb.metadata.creation_timestamp.isoformat() if crb.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': crb.metadata.deletion_timestamp.isoformat() if pending_deletion and crb.metadata.deletion_timestamp else None,
                'finalizers': crb.metadata.finalizers if pending_deletion and crb.metadata.finalizers else []
            })

        # Format CronJobs
        cronjob_list = []
        for cj in cronjobs.items:
            is_orphaned = False
            pending_deletion = is_pending_deletion(cj)
            
            schedule = cj.spec.schedule if cj.spec.schedule else 'Unknown'
            suspend = cj.spec.suspend if cj.spec.suspend else False
            last_schedule = cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else 'Never'
            
            cronjob_list.append({
                'name': cj.metadata.name,
                'namespace': cj.metadata.namespace,
                'schedule': schedule,
                'suspend': suspend,
                'lastSchedule': last_schedule,
                'age': cj.metadata.creation_timestamp.isoformat() if cj.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': cj.metadata.deletion_timestamp.isoformat() if pending_deletion and cj.metadata.deletion_timestamp else None,
                'finalizers': cj.metadata.finalizers if pending_deletion and cj.metadata.finalizers else []
            })
        
        # Format DaemonSets
        daemonset_list = []
        for ds in daemonsets.items:
            is_orphaned = not ds.metadata.owner_references
            pending_deletion = is_pending_deletion(ds)
            
            desired = ds.status.desired_number_scheduled or 0
            current = ds.status.current_number_scheduled or 0
            ready = ds.status.number_ready or 0
            
            daemonset_list.append({
                'name': ds.metadata.name,
                'namespace': ds.metadata.namespace,
                'desired': desired,
                'current': current,
                'ready': ready,
                'age': ds.metadata.creation_timestamp.isoformat() if ds.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ds.metadata.deletion_timestamp.isoformat() if pending_deletion and ds.metadata.deletion_timestamp else None,
                'finalizers': ds.metadata.finalizers if pending_deletion and ds.metadata.finalizers else []
            })
        
        # Format Ingresses
        ingress_list = []
        for ing in ingresses.items:
            is_orphaned = not ing.metadata.owner_references
            pending_deletion = is_pending_deletion(ing)
            
            ingress_class = ing.spec.ingress_class_name if ing.spec.ingress_class_name else 'default'
            
            hosts = []
            if ing.spec.rules:
                for rule in ing.spec.rules:
                    if rule.host:
                        hosts.append(rule.host)
            hosts_str = ', '.join(hosts) if hosts else '*'
            
            ingress_list.append({
                'name': ing.metadata.name,
                'namespace': ing.metadata.namespace,
                'class': ingress_class,
                'hosts': hosts_str,
                'age': ing.metadata.creation_timestamp.isoformat() if ing.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ing.metadata.deletion_timestamp.isoformat() if pending_deletion and ing.metadata.deletion_timestamp else None,
                'finalizers': ing.metadata.finalizers if pending_deletion and ing.metadata.finalizers else []
            })
        
        # Format Jobs
        job_list = []
        for job in jobs.items:
            is_orphaned = not job.metadata.owner_references
            pending_deletion = is_pending_deletion(job)
            
            completions = job.spec.completions or 1
            succeeded = job.status.succeeded or 0
            failed = job.status.failed or 0
            
            job_list.append({
                'name': job.metadata.name,
                'namespace': job.metadata.namespace,
                'completions': f"{succeeded}/{completions}",
                'failed': failed,
                'age': job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': job.metadata.deletion_timestamp.isoformat() if pending_deletion and job.metadata.deletion_timestamp else None,
                'finalizers': job.metadata.finalizers if pending_deletion and job.metadata.finalizers else []
            })
        
        # Format NetworkPolicies
        networkpolicy_list = []
        for np in networkpolicies.items:
            is_orphaned = not np.metadata.owner_references
            pending_deletion = is_pending_deletion(np)
            
            ingress_count = len(np.spec.ingress) if np.spec.ingress else 0
            egress_count = len(np.spec.egress) if np.spec.egress else 0
            
            networkpolicy_list.append({
                'name': np.metadata.name,
                'namespace': np.metadata.namespace,
                'ingress': ingress_count,
                'egress': egress_count,
                'age': np.metadata.creation_timestamp.isoformat() if np.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': np.metadata.deletion_timestamp.isoformat() if pending_deletion and np.metadata.deletion_timestamp else None,
                'finalizers': np.metadata.finalizers if pending_deletion and np.metadata.finalizers else []
            })
        
        # Format Roles
        role_list = []
        for role in roles.items:
            is_orphaned = True
            for rb in rolebindings.items:
                if rb.role_ref and rb.role_ref.kind == 'Role' and rb.role_ref.name == role.metadata.name and rb.metadata.namespace == role.metadata.namespace:
                    is_orphaned = False
                    break
            
            pending_deletion = is_pending_deletion(role)
            rules_count = len(role.rules) if role.rules else 0
            
            role_list.append({
                'name': role.metadata.name,
                'namespace': role.metadata.namespace,
                'rules': rules_count,
                'age': role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': role.metadata.deletion_timestamp.isoformat() if pending_deletion and role.metadata.deletion_timestamp else None,
                'finalizers': role.metadata.finalizers if pending_deletion and role.metadata.finalizers else []
            })
        
        # Format RoleBindings
        rolebinding_list = []
        for rb in rolebindings.items:
            is_orphaned = not rb.subjects or len(rb.subjects) == 0
            
            if not is_orphaned and rb.role_ref:
                if rb.role_ref.kind == 'Role':
                    role_exists = any(r.metadata.name == rb.role_ref.name and r.metadata.namespace == rb.metadata.namespace for r in roles.items)
                    if not role_exists:
                        is_orphaned = True
            
            pending_deletion = is_pending_deletion(rb)
            
            role_name = rb.role_ref.name if rb.role_ref else 'Unknown'
            role_kind = rb.role_ref.kind if rb.role_ref else 'Unknown'
            subjects_count = len(rb.subjects) if rb.subjects else 0
            
            first_subject = ''
            if rb.subjects and len(rb.subjects) > 0:
                subj = rb.subjects[0]
                if subj.kind == 'ServiceAccount':
                    first_subject = f"{subj.kind}:{subj.namespace}/{subj.name}" if subj.namespace else f"{subj.kind}:{subj.name}"
                else:
                    first_subject = f"{subj.kind}:{subj.name}"
                if subjects_count > 1:
                    first_subject += f" (+{subjects_count - 1} more)"
            
            rolebinding_list.append({
                'name': rb.metadata.name,
                'namespace': rb.metadata.namespace,
                'role': role_name,
                'roleKind': role_kind,
                'subjects': first_subject,
                'subjectsCount': subjects_count,
                'age': rb.metadata.creation_timestamp.isoformat() if rb.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': rb.metadata.deletion_timestamp.isoformat() if pending_deletion and rb.metadata.deletion_timestamp else None,
                'finalizers': rb.metadata.finalizers if pending_deletion and rb.metadata.finalizers else []
            })
        
        # Format StorageClasses
        storageclass_list = []
        for sc in storageclasses.items:
            is_orphaned = False
            pending_deletion = is_pending_deletion(sc)
            
            provisioner = sc.provisioner if sc.provisioner else 'Unknown'
            reclaim_policy = sc.reclaim_policy if sc.reclaim_policy else 'Delete'
            volume_binding_mode = sc.volume_binding_mode if sc.volume_binding_mode else 'Immediate'
            
            storageclass_list.append({
                'name': sc.metadata.name,
                'provisioner': provisioner,
                'reclaimPolicy': reclaim_policy,
                'volumeBindingMode': volume_binding_mode,
                'age': sc.metadata.creation_timestamp.isoformat() if sc.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': sc.metadata.deletion_timestamp.isoformat() if pending_deletion and sc.metadata.deletion_timestamp else None,
                'finalizers': sc.metadata.finalizers if pending_deletion and sc.metadata.finalizers else []
            })

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.3.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'version': '3.3.0'
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
            'message': f'Successfully scaled {resource_type} {namespace}/{deployment_name} to {replicas} replicas',
            'replicas': replicas
        }), 200
        
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
        batch_v1 = client.BatchV1Api()
        networking_v1 = client.NetworkingV1Api()
        rbac_v1 = client.RbacAuthorizationV1Api()
        storage_v1 = client.StorageV1Api()
        
        configmaps = v1.list_config_map_for_all_namespaces()
        cronjobs = batch_v1.list_cron_job_for_all_namespaces()
        daemonsets = apps_v1.list_daemon_set_for_all_namespaces()
        deployments = apps_v1.list_deployment_for_all_namespaces()
        ingresses = networking_v1.list_ingress_for_all_namespaces()
        jobs = batch_v1.list_job_for_all_namespaces()
        networkpolicies = networking_v1.list_network_policy_for_all_namespaces()
        pods = v1.list_pod_for_all_namespaces()
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        pvs = v1.list_persistent_volume()
        replicasets = apps_v1.list_replica_set_for_all_namespaces()
        rolebindings = rbac_v1.list_role_binding_for_all_namespaces()
        roles = rbac_v1.list_role_for_all_namespaces()
        secrets = v1.list_secret_for_all_namespaces()
        service_accounts = v1.list_service_account_for_all_namespaces()
        services = v1.list_service_for_all_namespaces()
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        storageclasses = storage_v1.list_storage_class()
        
        # Additional resources
        limitranges = v1.list_limit_range_for_all_namespaces()
        resourcequotas = v1.list_resource_quota_for_all_namespaces()
        
        # Autoscaling and Policy resources
        autoscaling_v1 = client.AutoscalingV1Api()
        policy_v1 = client.PolicyV1Api()
        
        endpoints = v1.list_endpoints_for_all_namespaces()
        horizontalpodautoscalers = autoscaling_v1.list_horizontal_pod_autoscaler_for_all_namespaces()
        namespaces = v1.list_namespace()
        poddisruptionbudgets = policy_v1.list_pod_disruption_budget_for_all_namespaces()
        
        # VolumeSnapshots (requires snapshot.storage.k8s.io API)
        volumesnapshots = []
        volumesnapshotcontents = []
        try:
            snapshot_v1 = client.CustomObjectsApi()
            vs_result = snapshot_v1.list_cluster_custom_object(
                group='snapshot.storage.k8s.io',
                version='v1',
                plural='volumesnapshots'
            )
            volumesnapshots = vs_result.get('items', [])
        except:
            pass
        
        try:
            vsc_result = snapshot_v1.list_cluster_custom_object(
                group='snapshot.storage.k8s.io',
                version='v1',
                plural='volumesnapshotcontents'
            )
            volumesnapshotcontents = vsc_result.get('items', [])
        except:
            pass
        
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
        
        
        # Format ClusterRoles
        clusterrole_list = []
        cluster_roles = []
        try:
            cluster_roles = rbac_v1.list_cluster_role().items
        except:
            pass
        
        for cr in cluster_roles:
            # Check if orphaned (not referenced by any ClusterRoleBinding or RoleBinding)
            is_orphaned = True
            
            # Check ClusterRoleBindings
            for crb in cluster_role_bindings:
                if crb.role_ref and crb.role_ref.kind == 'ClusterRole' and crb.role_ref.name == cr.metadata.name:
                    is_orphaned = False
                    break
            
            # Check RoleBindings (can also reference ClusterRoles)
            if is_orphaned:
                for rb in role_bindings:
                    if rb.role_ref and rb.role_ref.kind == 'ClusterRole' and rb.role_ref.name == cr.metadata.name:
                        is_orphaned = False
                        break
            
            # System ClusterRoles are not orphaned
            is_system = cr.metadata.name.startswith('system:') or cr.metadata.name.startswith('cluster-')
            if is_system:
                is_orphaned = False
            
            pending_deletion = is_pending_deletion(cr)
            
            # Count rules
            rules_count = len(cr.rules) if cr.rules else 0
            
            clusterrole_list.append({
                'name': cr.metadata.name,
                'rules': rules_count,
                'age': cr.metadata.creation_timestamp.isoformat() if cr.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': cr.metadata.deletion_timestamp.isoformat() if pending_deletion and cr.metadata.deletion_timestamp else None,
                'finalizers': cr.metadata.finalizers if pending_deletion and cr.metadata.finalizers else []
            })
        
        # Format ClusterRoleBindings
        clusterrolebinding_list = []
        for crb in cluster_role_bindings:
            # Check if orphaned (no subjects or role doesn't exist)
            is_orphaned = not crb.subjects or len(crb.subjects) == 0
            
            # Check if the referenced ClusterRole exists
            if not is_orphaned and crb.role_ref:
                role_exists = any(cr.metadata.name == crb.role_ref.name for cr in cluster_roles)
                if not role_exists:
                    is_orphaned = True
            
            pending_deletion = is_pending_deletion(crb)
            
            # Get role name and subjects
            role_name = crb.role_ref.name if crb.role_ref else 'Unknown'
            subjects_count = len(crb.subjects) if crb.subjects else 0
            
            # Get first subject for display
            first_subject = ''
            if crb.subjects and len(crb.subjects) > 0:
                subj = crb.subjects[0]
                if subj.kind == 'ServiceAccount':
                    first_subject = f"{subj.kind}:{subj.namespace}/{subj.name}" if subj.namespace else f"{subj.kind}:{subj.name}"
                else:
                    first_subject = f"{subj.kind}:{subj.name}"
                if subjects_count > 1:
                    first_subject += f" (+{subjects_count - 1} more)"
            
            clusterrolebinding_list.append({
                'name': crb.metadata.name,
                'role': role_name,
                'subjects': first_subject,
                'subjectsCount': subjects_count,
                'age': crb.metadata.creation_timestamp.isoformat() if crb.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': crb.metadata.deletion_timestamp.isoformat() if pending_deletion and crb.metadata.deletion_timestamp else None,
                'finalizers': crb.metadata.finalizers if pending_deletion and crb.metadata.finalizers else []
            })

        # Format CronJobs
        cronjob_list = []
        for cj in cronjobs.items:
            is_orphaned = False
            pending_deletion = is_pending_deletion(cj)
            
            schedule = cj.spec.schedule if cj.spec.schedule else 'Unknown'
            suspend = cj.spec.suspend if cj.spec.suspend else False
            last_schedule = cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else 'Never'
            
            cronjob_list.append({
                'name': cj.metadata.name,
                'namespace': cj.metadata.namespace,
                'schedule': schedule,
                'suspend': suspend,
                'lastSchedule': last_schedule,
                'age': cj.metadata.creation_timestamp.isoformat() if cj.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': cj.metadata.deletion_timestamp.isoformat() if pending_deletion and cj.metadata.deletion_timestamp else None,
                'finalizers': cj.metadata.finalizers if pending_deletion and cj.metadata.finalizers else []
            })
        
        # Format DaemonSets
        daemonset_list = []
        for ds in daemonsets.items:
            is_orphaned = not ds.metadata.owner_references
            pending_deletion = is_pending_deletion(ds)
            
            desired = ds.status.desired_number_scheduled or 0
            current = ds.status.current_number_scheduled or 0
            ready = ds.status.number_ready or 0
            
            daemonset_list.append({
                'name': ds.metadata.name,
                'namespace': ds.metadata.namespace,
                'desired': desired,
                'current': current,
                'ready': ready,
                'age': ds.metadata.creation_timestamp.isoformat() if ds.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ds.metadata.deletion_timestamp.isoformat() if pending_deletion and ds.metadata.deletion_timestamp else None,
                'finalizers': ds.metadata.finalizers if pending_deletion and ds.metadata.finalizers else []
            })
        
        # Format Endpoints
        endpoint_list = []
        for ep in endpoints.items:
            is_orphaned = not ep.metadata.owner_references
            pending_deletion = is_pending_deletion(ep)
            
            # Count subsets and addresses
            subsets_count = len(ep.subsets) if ep.subsets else 0
            addresses_count = 0
            if ep.subsets:
                for subset in ep.subsets:
                    if subset.addresses:
                        addresses_count += len(subset.addresses)
            
            endpoint_list.append({
                'name': ep.metadata.name,
                'namespace': ep.metadata.namespace,
                'subsets': subsets_count,
                'addresses': addresses_count,
                'age': ep.metadata.creation_timestamp.isoformat() if ep.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ep.metadata.deletion_timestamp.isoformat() if pending_deletion and ep.metadata.deletion_timestamp else None,
                'finalizers': ep.metadata.finalizers if pending_deletion and ep.metadata.finalizers else []
            })

        # Format HorizontalPodAutoscalers
        hpa_list = []
        for hpa in horizontalpodautoscalers.items:
            # Check if orphaned (target doesn't exist)
            is_orphaned = False
            target_ref = hpa.spec.scale_target_ref
            
            if target_ref:
                target_kind = target_ref.kind
                target_name = target_ref.name
                target_namespace = hpa.metadata.namespace
                
                # Check if target exists
                if target_kind == 'Deployment':
                    target_exists = any(d.metadata.name == target_name and d.metadata.namespace == target_namespace for d in deployments.items)
                    is_orphaned = not target_exists
                elif target_kind == 'StatefulSet':
                    target_exists = any(s.metadata.name == target_name and s.metadata.namespace == target_namespace for s in statefulsets.items)
                    is_orphaned = not target_exists
                elif target_kind == 'ReplicaSet':
                    target_exists = any(r.metadata.name == target_name and r.metadata.namespace == target_namespace for r in replicasets.items)
                    is_orphaned = not target_exists
            
            pending_deletion = is_pending_deletion(hpa)
            
            # Get current/desired replicas
            current_replicas = hpa.status.current_replicas if hpa.status and hpa.status.current_replicas else 0
            desired_replicas = hpa.status.desired_replicas if hpa.status and hpa.status.desired_replicas else 0
            
            # Get target reference
            target = f"{target_ref.kind}/{target_ref.name}" if target_ref else 'Unknown'
            
            hpa_list.append({
                'name': hpa.metadata.name,
                'namespace': hpa.metadata.namespace,
                'target': target,
                'minReplicas': hpa.spec.min_replicas if hpa.spec.min_replicas else 1,
                'maxReplicas': hpa.spec.max_replicas,
                'currentReplicas': current_replicas,
                'desiredReplicas': desired_replicas,
                'age': hpa.metadata.creation_timestamp.isoformat() if hpa.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': hpa.metadata.deletion_timestamp.isoformat() if pending_deletion and hpa.metadata.deletion_timestamp else None,
                'finalizers': hpa.metadata.finalizers if pending_deletion and hpa.metadata.finalizers else []
            })

        # Format Namespaces
        namespace_list = []
        for ns in namespaces.items:
            # Check if orphaned (empty namespace with no resources)
            is_orphaned = False
            
            # Count resources in this namespace
            resource_count = 0
            resource_count += sum(1 for p in pods.items if p.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for d in deployments.items if d.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for s in statefulsets.items if s.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for ds in daemonsets.items if ds.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for cm in configmaps.items if cm.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for sec in secrets.items if sec.metadata.namespace == ns.metadata.name)
            resource_count += sum(1 for svc in services.items if svc.metadata.namespace == ns.metadata.name)
            
            # Namespace is orphaned if it's empty and not a system namespace
            system_namespaces = ['default', 'kube-system', 'kube-public', 'kube-node-lease']
            if resource_count == 0 and ns.metadata.name not in system_namespaces:
                is_orphaned = True
            
            pending_deletion = is_pending_deletion(ns)
            
            # Get phase
            phase = ns.status.phase if ns.status and ns.status.phase else 'Unknown'
            
            namespace_list.append({
                'name': ns.metadata.name,
                'phase': phase,
                'resourceCount': resource_count,
                'age': ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ns.metadata.deletion_timestamp.isoformat() if pending_deletion and ns.metadata.deletion_timestamp else None,
                'finalizers': ns.metadata.finalizers if pending_deletion and ns.metadata.finalizers else []
            })

        # Format PodDisruptionBudgets
        pdb_list = []
        for pdb in poddisruptionbudgets.items:
            # Check if orphaned (no matching pods via label selector)
            is_orphaned = False
            
            if pdb.spec.selector and pdb.spec.selector.match_labels:
                # Check if any pods match the selector in the same namespace
                matching_pods = False
                for pod in pods.items:
                    if pod.metadata.namespace == pdb.metadata.namespace:
                        if pod.metadata.labels:
                            # Check if all selector labels match
                            all_match = all(
                                pod.metadata.labels.get(k) == v 
                                for k, v in pdb.spec.selector.match_labels.items()
                            )
                            if all_match:
                                matching_pods = True
                                break
                
                is_orphaned = not matching_pods
            
            pending_deletion = is_pending_deletion(pdb)
            
            # Get disruption info
            min_available = pdb.spec.min_available if pdb.spec.min_available else '-'
            max_unavailable = pdb.spec.max_unavailable if pdb.spec.max_unavailable else '-'
            current_healthy = pdb.status.current_healthy if pdb.status and pdb.status.current_healthy is not None else 0
            desired_healthy = pdb.status.desired_healthy if pdb.status and pdb.status.desired_healthy is not None else 0
            
            pdb_list.append({
                'name': pdb.metadata.name,
                'namespace': pdb.metadata.namespace,
                'minAvailable': str(min_available),
                'maxUnavailable': str(max_unavailable),
                'currentHealthy': current_healthy,
                'desiredHealthy': desired_healthy,
                'age': pdb.metadata.creation_timestamp.isoformat() if pdb.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': pdb.metadata.deletion_timestamp.isoformat() if pending_deletion and pdb.metadata.deletion_timestamp else None,
                'finalizers': pdb.metadata.finalizers if pending_deletion and pdb.metadata.finalizers else []
            })

        # Format Ingresses
        ingress_list = []
        for ing in ingresses.items:
            is_orphaned = not ing.metadata.owner_references
            pending_deletion = is_pending_deletion(ing)
            
            ingress_class = ing.spec.ingress_class_name if ing.spec.ingress_class_name else 'default'
            
            hosts = []
            if ing.spec.rules:
                for rule in ing.spec.rules:
                    if rule.host:
                        hosts.append(rule.host)
            hosts_str = ', '.join(hosts) if hosts else '*'
            
            ingress_list.append({
                'name': ing.metadata.name,
                'namespace': ing.metadata.namespace,
                'class': ingress_class,
                'hosts': hosts_str,
                'age': ing.metadata.creation_timestamp.isoformat() if ing.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': ing.metadata.deletion_timestamp.isoformat() if pending_deletion and ing.metadata.deletion_timestamp else None,
                'finalizers': ing.metadata.finalizers if pending_deletion and ing.metadata.finalizers else []
            })
        
        # Format Jobs
        job_list = []
        for job in jobs.items:
            is_orphaned = not job.metadata.owner_references
            pending_deletion = is_pending_deletion(job)
            
            completions = job.spec.completions or 1
            succeeded = job.status.succeeded or 0
            failed = job.status.failed or 0
            
            job_list.append({
                'name': job.metadata.name,
                'namespace': job.metadata.namespace,
                'completions': f"{succeeded}/{completions}",
                'failed': failed,
                'age': job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': job.metadata.deletion_timestamp.isoformat() if pending_deletion and job.metadata.deletion_timestamp else None,
                'finalizers': job.metadata.finalizers if pending_deletion and job.metadata.finalizers else []
            })
        
        # Format NetworkPolicies
        networkpolicy_list = []
        for np in networkpolicies.items:
            is_orphaned = not np.metadata.owner_references
            pending_deletion = is_pending_deletion(np)
            
            ingress_count = len(np.spec.ingress) if np.spec.ingress else 0
            egress_count = len(np.spec.egress) if np.spec.egress else 0
            
            networkpolicy_list.append({
                'name': np.metadata.name,
                'namespace': np.metadata.namespace,
                'ingress': ingress_count,
                'egress': egress_count,
                'age': np.metadata.creation_timestamp.isoformat() if np.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': np.metadata.deletion_timestamp.isoformat() if pending_deletion and np.metadata.deletion_timestamp else None,
                'finalizers': np.metadata.finalizers if pending_deletion and np.metadata.finalizers else []
            })
        
        # Format Roles
        role_list = []
        for role in roles.items:
            is_orphaned = True
            for rb in rolebindings.items:
                if rb.role_ref and rb.role_ref.kind == 'Role' and rb.role_ref.name == role.metadata.name and rb.metadata.namespace == role.metadata.namespace:
                    is_orphaned = False
                    break
            
            pending_deletion = is_pending_deletion(role)
            rules_count = len(role.rules) if role.rules else 0
            
            role_list.append({
                'name': role.metadata.name,
                'namespace': role.metadata.namespace,
                'rules': rules_count,
                'age': role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': role.metadata.deletion_timestamp.isoformat() if pending_deletion and role.metadata.deletion_timestamp else None,
                'finalizers': role.metadata.finalizers if pending_deletion and role.metadata.finalizers else []
            })
        
        # Format RoleBindings
        rolebinding_list = []
        for rb in rolebindings.items:
            is_orphaned = not rb.subjects or len(rb.subjects) == 0
            
            if not is_orphaned and rb.role_ref:
                if rb.role_ref.kind == 'Role':
                    role_exists = any(r.metadata.name == rb.role_ref.name and r.metadata.namespace == rb.metadata.namespace for r in roles.items)
                    if not role_exists:
                        is_orphaned = True
            
            pending_deletion = is_pending_deletion(rb)
            
            role_name = rb.role_ref.name if rb.role_ref else 'Unknown'
            role_kind = rb.role_ref.kind if rb.role_ref else 'Unknown'
            subjects_count = len(rb.subjects) if rb.subjects else 0
            
            first_subject = ''
            if rb.subjects and len(rb.subjects) > 0:
                subj = rb.subjects[0]
                if subj.kind == 'ServiceAccount':
                    first_subject = f"{subj.kind}:{subj.namespace}/{subj.name}" if subj.namespace else f"{subj.kind}:{subj.name}"
                else:
                    first_subject = f"{subj.kind}:{subj.name}"
                if subjects_count > 1:
                    first_subject += f" (+{subjects_count - 1} more)"
            
            rolebinding_list.append({
                'name': rb.metadata.name,
                'namespace': rb.metadata.namespace,
                'role': role_name,
                'roleKind': role_kind,
                'subjects': first_subject,
                'subjectsCount': subjects_count,
                'age': rb.metadata.creation_timestamp.isoformat() if rb.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': rb.metadata.deletion_timestamp.isoformat() if pending_deletion and rb.metadata.deletion_timestamp else None,
                'finalizers': rb.metadata.finalizers if pending_deletion and rb.metadata.finalizers else []
            })
        
        # Format StorageClasses
        storageclass_list = []
        for sc in storageclasses.items:
            is_orphaned = False
            pending_deletion = is_pending_deletion(sc)
            
            provisioner = sc.provisioner if sc.provisioner else 'Unknown'
            reclaim_policy = sc.reclaim_policy if sc.reclaim_policy else 'Delete'
            volume_binding_mode = sc.volume_binding_mode if sc.volume_binding_mode else 'Immediate'
            
            storageclass_list.append({
                'name': sc.metadata.name,
                'provisioner': provisioner,
                'reclaimPolicy': reclaim_policy,
                'volumeBindingMode': volume_binding_mode,
                'age': sc.metadata.creation_timestamp.isoformat() if sc.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': sc.metadata.deletion_timestamp.isoformat() if pending_deletion and sc.metadata.deletion_timestamp else None,
                'finalizers': sc.metadata.finalizers if pending_deletion and sc.metadata.finalizers else []
            })


        # Format LimitRanges
        limitrange_list = []
        for lr in limitranges.items:
            is_orphaned = not lr.metadata.owner_references
            pending_deletion = is_pending_deletion(lr)
            
            limits_count = len(lr.spec.limits) if lr.spec.limits else 0
            
            limitrange_list.append({
                'name': lr.metadata.name,
                'namespace': lr.metadata.namespace,
                'limits': limits_count,
                'age': lr.metadata.creation_timestamp.isoformat() if lr.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': lr.metadata.deletion_timestamp.isoformat() if pending_deletion and lr.metadata.deletion_timestamp else None,
                'finalizers': lr.metadata.finalizers if pending_deletion and lr.metadata.finalizers else []
            })
        
        # Format ResourceQuotas
        resourcequota_list = []
        for rq in resourcequotas.items:
            is_orphaned = not rq.metadata.owner_references
            pending_deletion = is_pending_deletion(rq)
            
            hard_count = len(rq.spec.hard) if rq.spec.hard else 0
            
            resourcequota_list.append({
                'name': rq.metadata.name,
                'namespace': rq.metadata.namespace,
                'hardLimits': hard_count,
                'age': rq.metadata.creation_timestamp.isoformat() if rq.metadata.creation_timestamp else '',
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': rq.metadata.deletion_timestamp.isoformat() if pending_deletion and rq.metadata.deletion_timestamp else None,
                'finalizers': rq.metadata.finalizers if pending_deletion and rq.metadata.finalizers else []
            })
        
        # Format VolumeSnapshots
        volumesnapshot_list = []
        for vs in volumesnapshots:
            metadata = vs.get('metadata', {})
            spec = vs.get('spec', {})
            status = vs.get('status', {})
            
            is_orphaned = not metadata.get('ownerReferences')
            pending_deletion = metadata.get('deletionTimestamp') is not None
            
            source_pvc = spec.get('source', {}).get('persistentVolumeClaimName', 'Unknown')
            ready = status.get('readyToUse', False)
            
            volumesnapshot_list.append({
                'name': metadata.get('name', 'Unknown'),
                'namespace': metadata.get('namespace', 'Unknown'),
                'sourcePVC': source_pvc,
                'ready': ready,
                'age': metadata.get('creationTimestamp', ''),
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': metadata.get('deletionTimestamp'),
                'finalizers': metadata.get('finalizers', []) if pending_deletion else []
            })
        
        # Format VolumeSnapshotContents
        volumesnapshotcontent_list = []
        for vsc in volumesnapshotcontents:
            metadata = vsc.get('metadata', {})
            spec = vsc.get('spec', {})
            status = vsc.get('status', {})
            
            is_orphaned = not metadata.get('ownerReferences')
            pending_deletion = metadata.get('deletionTimestamp') is not None
            
            snapshot_ref = spec.get('volumeSnapshotRef', {}).get('name', 'Unknown')
            ready = status.get('readyToUse', False)
            
            volumesnapshotcontent_list.append({
                'name': metadata.get('name', 'Unknown'),
                'snapshotRef': snapshot_ref,
                'ready': ready,
                'age': metadata.get('creationTimestamp', ''),
                'orphaned': is_orphaned,
                'pendingDeletion': pending_deletion,
                'deletionTimestamp': metadata.get('deletionTimestamp'),
                'finalizers': metadata.get('finalizers', []) if pending_deletion else []
            })

        return jsonify({
            'applications': application_list,
            'clusterrolebindings': clusterrolebinding_list,
            'clusterroles': clusterrole_list,
            'configmaps': configmap_list,
            'cronjobs': cronjob_list,
            'daemonsets': daemonset_list,
            'deployments': deployment_list,
            'endpoints': endpoint_list,
            'horizontalpodautoscalers': hpa_list,
            'ingresses': ingress_list,
            'jobs': job_list,
            'limitranges': limitrange_list,
            'namespaces': namespace_list,
            'networkpolicies': networkpolicy_list,
            'poddisruptionbudgets': pdb_list,
            'pods': pod_list,
            'protection_plans': plan_list,
            'pvcs': pvc_list,
            'pvs': pv_list,
            'replicasets': replicaset_list,
            'resourcequotas': resourcequota_list,
            'rolebindings': rolebinding_list,
            'roles': role_list,
            'secrets': secret_list,
            'serviceaccounts': serviceaccount_list,
            'services': service_list,
            'snapshots': snapshot_list,
            'statefulsets': statefulset_list,
            'storageclasses': storageclass_list,
            'volumesnapshotcontents': volumesnapshotcontent_list,
            'volumesnapshots': volumesnapshot_list,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error getting resources: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
