"""
Kubernetes cluster data retrieval functions
"""
import os
import json
import time
from datetime import datetime
import pytz
from kubernetes import client, config

# Load Kubernetes config
try:
    config.load_incluster_config()
    print("Loaded in-cluster Kubernetes config")
except Exception as e:
    print(f"Failed to load in-cluster config: {e}")
    try:
        config.load_kube_config()
        print("Loaded local Kubernetes config")
    except Exception as e2:
        print(f"Failed to load any Kubernetes config: {e2}")

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def get_cluster_data():
    try:
        # Get nodes
        nodes = v1.list_node()
        
        # Get pods
        pods = v1.list_pod_for_all_namespaces()
        
        # Get deployments
        deployments = apps_v1.list_deployment_for_all_namespaces()
        
        # Get statefulsets
        statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
        
        # Get services
        services = v1.list_service_for_all_namespaces()
        
        # Process nodes
        master_nodes = []
        worker_nodes = []
        worker_pools = {}
        
        for node in nodes.items:
            node_info = {
                'name': node.metadata.name,
                'status': 'Ready' if any(condition.type == 'Ready' and condition.status == 'True' 
                                       for condition in node.status.conditions) else 'NotReady',
                'roles': [],
                'version': node.status.node_info.kubelet_version,
                'os': node.status.node_info.os_image,
                'container_runtime': node.status.node_info.container_runtime_version,
                'cpu_capacity': node.status.capacity.get('cpu', 'Unknown'),
                'memory_capacity': node.status.capacity.get('memory', 'Unknown'),
                'pods': [],
                'internal_ip': None,
                'external_ip': None
            }
            
            # Get node IPs
            if node.status.addresses:
                for addr in node.status.addresses:
                    if addr.type == 'InternalIP':
                        node_info['internal_ip'] = addr.address
                    elif addr.type == 'ExternalIP':
                        node_info['external_ip'] = addr.address
            
            # Determine node roles
            if node.metadata.labels:
                if 'node-role.kubernetes.io/control-plane' in node.metadata.labels or \
                   'node-role.kubernetes.io/master' in node.metadata.labels:
                    node_info['roles'].append('control-plane')
                    master_nodes.append(node_info)
                else:
                    node_info['roles'].append('worker')
                    
                    # Group worker nodes by pool based on node name patterns
                    pool_name = 'default-pool'
                    if 'nkp-dev-worker-pool' in node.metadata.name:
                        pool_name = 'nkp-dev-worker-pool'
                    elif 'worker-pool' in node.metadata.name:
                        pool_name = 'worker-pool'
                    elif 'worker-0' in node.metadata.name:
                        pool_name = 'nkp-dev016f2162781410-worker-pool'
                    
                    if pool_name not in worker_pools:
                        worker_pools[pool_name] = []
                    worker_pools[pool_name].append(node_info)
        
        # Add pods to nodes
        for pod in pods.items:
            if pod.spec.node_name and pod.status.phase not in ['Succeeded', 'Failed']:
                pod_info = {
                    'name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'status': pod.status.phase,
                    'cpu_request': '0',
                    'memory_request': '0',
                    'labels': pod.metadata.labels or {}
                }
                
                # Calculate resource requests
                if pod.spec.containers:
                    for container in pod.spec.containers:
                        if container.resources and container.resources.requests:
                            if 'cpu' in container.resources.requests:
                                pod_info['cpu_request'] = container.resources.requests['cpu']
                            if 'memory' in container.resources.requests:
                                pod_info['memory_request'] = container.resources.requests['memory']
                
                # Add pod to appropriate node
                for master in master_nodes:
                    if master['name'] == pod.spec.node_name:
                        master['pods'].append(pod_info)
                        break
                
                for pool_nodes in worker_pools.values():
                    for worker in pool_nodes:
                        if worker['name'] == pod.spec.node_name:
                            worker['pods'].append(pod_info)
                            break
        
        # Process deployments
        deployment_info = []
        for deployment in deployments.items:
            dep_info = {
                'name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'replicas': deployment.spec.replicas or 0,
                'ready_replicas': deployment.status.ready_replicas or 0,
                'available_replicas': deployment.status.available_replicas or 0,
                'labels': deployment.metadata.labels or {},
                'selector': deployment.spec.selector.match_labels or {},
                'type': 'Deployment'
            }
            deployment_info.append(dep_info)
        
        # Process statefulsets
        for statefulset in statefulsets.items:
            sts_info = {
                'name': statefulset.metadata.name,
                'namespace': statefulset.metadata.namespace,
                'replicas': statefulset.spec.replicas or 0,
                'ready_replicas': statefulset.status.ready_replicas or 0,
                'available_replicas': statefulset.status.ready_replicas or 0,  # StatefulSets don't have available_replicas
                'labels': statefulset.metadata.labels or {},
                'selector': statefulset.spec.selector.match_labels or {},
                'type': 'StatefulSet'
            }
            deployment_info.append(sts_info)
        
        # Process services
        service_info = []
        for service in services.items:
            svc_info = {
                'name': service.metadata.name,
                'namespace': service.metadata.namespace,
                'type': service.spec.type,
                'cluster_ip': service.spec.cluster_ip,
                'external_ips': service.spec.external_i_ps or [],
                'ports': [],
                'selector': service.spec.selector or {},
                'load_balancer_ip': None
            }
            
            # Get ports
            if service.spec.ports:
                for port in service.spec.ports:
                    svc_info['ports'].append({
                        'name': port.name,
                        'port': port.port,
                        'target_port': port.target_port,
                        'protocol': port.protocol
                    })
            
            # Get LoadBalancer IP
            if service.status.load_balancer and service.status.load_balancer.ingress:
                for ingress in service.status.load_balancer.ingress:
                    if ingress.ip:
                        svc_info['load_balancer_ip'] = ingress.ip
                        break
            
            service_info.append(svc_info)
        
        # Calculate totals
        total_nodes = len(nodes.items)
        ready_nodes = sum(1 for node in nodes.items 
                        if any(condition.type == 'Ready' and condition.status == 'True' 
                              for condition in node.status.conditions))
        total_pods = len([pod for pod in pods.items if pod.status.phase not in ['Succeeded', 'Failed']])
        running_pods = len([pod for pod in pods.items if pod.status.phase == 'Running'])
        
        return {
            'cluster_name': os.environ.get('CLUSTER_NAME', 'nkp-dev01'),
            'kubernetes_version': nodes.items[0].status.node_info.kubelet_version if nodes.items else 'Unknown',
            'total_nodes': total_nodes,
            'ready_nodes': ready_nodes,
            'total_pods': total_pods,
            'running_pods': running_pods,
            'master_nodes': master_nodes,
            'worker_pools': worker_pools,
            'deployments': deployment_info,
            'services': service_info,
            'last_updated': datetime.now(pytz.timezone('America/New_York')).isoformat()
        }
    except Exception as e:
        print(f"Error getting cluster data: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'cluster_name': os.environ.get('CLUSTER_NAME', 'nkp-dev01'),
            'kubernetes_version': 'Unknown',
            'total_nodes': 0,
            'ready_nodes': 0,
            'total_pods': 0,
            'running_pods': 0,
            'master_nodes': [],
            'worker_pools': {},
            'deployments': [],
            'services': [],
            'last_updated': datetime.now(pytz.timezone('America/New_York')).isoformat()
        }


