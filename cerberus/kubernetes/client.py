import yaml
import logging
from collections import defaultdict
from kubernetes import client, config
import cerberus.invoke.command as runcommand
from kubernetes.client.rest import ApiException
import requests
from urllib3.exceptions import InsecureRequestWarning
import cerberus.redis.client as redis_cli


pods_tracker = defaultdict(dict)


# Load kubeconfig and initialize kubernetes python client
def initialize_clients(kubeconfig_path):
    global cli
    config.load_kube_config(kubeconfig_path)
    cli = client.CoreV1Api()


# Set redis cache expiry time
def redis_cache_expiry(time):
    global expiry_time
    expiry_time = time


# List nodes in the cluster
def list_nodes(label_selector=None):
    nodes = []
    if label_selector is None:
        node_key = 'nodes'
    else:
        node_key = 'nodes' + label_selector
    status = redis_cli.check_if_exists(node_key)
    if status == 0:
        try:
            if label_selector:
                ret = cli.list_node(pretty=True, label_selector=label_selector)
            else:
                ret = cli.list_node(pretty=True)
        except ApiException as e:
            logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)
        for node in ret.items:
            nodes.append(node.metadata.name)
            redis_cli.insert_sets(node_key, node.metadata.name)
        redis_cli.set_expiry(node_key, expiry_time)
    else:
        nodes = redis_cli.get_set_items(node_key)
    return nodes


# List pods in the given namespace
def list_pods(namespace):
    pods = []
    pods_key = 'pods' + namespace
    status = redis_cli.check_if_exists(pods_key)
    if status == 0:
        try:
            ret = cli.list_namespaced_pod(namespace, pretty=True)
        except ApiException as e:
            logging.error("Exception when calling \
                           CoreV1Api->list_namespaced_pod: %s\n" % e)
        for pod in ret.items:
            pods.append(pod.metadata.name)
            redis_cli.insert_sets(pods_key, pod.metadata.name)
        # Expire the key in cache after the specified time
        redis_cli.set_expiry(pods_key, expiry_time)
    else:
        pods = redis_cli.get_set_items(pods_key)
    return pods


# Get the list of namespaces
def list_namespaces():
    namespaces = []
    key = 'namespaces'
    status = redis_cli.check_if_exists(key)
    if status == 0:
        try:
            namespaces_list = cli.list_namespace()
        except ApiException as e:
            logging.error("Exception when calling \
                       CoreV1Api->list_namespaces: %s\n" % e)
        for namespace in namespaces_list.items:
            namespaces.append(namespace.metadata.name)
        for namespace in namespaces:
            redis_cli.insert_sets(key, namespace)
        # Expire the key in cache after the specified time
        redis_cli.set_expiry(key, expiry_time)
    else:
        namespaces = redis_cli.get_set_items(key)
    return namespaces


# Get pod status
def get_pod_status(pod, namespace):
    try:
        return cli.read_namespaced_pod_status(pod, namespace, pretty=True)
    except ApiException as e:
        logging.error("Exception when calling \
                      CoreV1Api->read_namespaced_pod_status: %s\n" % e)


# Monitor the status of the cluster nodes and set the status to true or false
def monitor_nodes():
    nodes = list_nodes()
    notready_nodes = []
    for node in nodes:
        node_kerneldeadlock_status = "False"
        try:
            node_info = cli.read_node_status(node, pretty=True)
        except ApiException as e:
            logging.error("Exception when calling \
                           CoreV1Api->read_node_status: %s\n" % e)
        for condition in node_info.status.conditions:
            if condition.type == "KernelDeadlock":
                node_kerneldeadlock_status = condition.status
            elif condition.type == "Ready":
                node_ready_status = condition.status
            else:
                continue
        if node_kerneldeadlock_status != "False" or node_ready_status != "True":
            notready_nodes.append(node)
    if len(notready_nodes) != 0:
        status = False
    else:
        status = True
    return status, notready_nodes


# Check the namespace name for default SDN
def check_sdn_namespace():
    namespaces = list_namespaces()
    for namespace in namespaces:
        if namespace == "openshift-ovn-kubernetes":
            return "openshift-ovn-kubernetes"
        elif namespace == "openshift-sdn":
            return "openshift-sdn"
        else:
            continue
    logging.error("Could not find openshift-sdn and openshift-ovn-kubernetes namespaces, \
        please specify the correct networking namespace in config file")


# Track the pods that were crashed/restarted during the sleep interval of an iteration
def namespace_sleep_tracker(namespace):
    global pods_tracker
    pods = list_pods(namespace)
    crashed_restarted_pods = defaultdict(list)
    for pod in pods:
        pod_info = get_pod_status(pod, namespace)
        pod_status = pod_info.status
        pod_status_phase = pod_status.phase
        pod_restart_count = 0
        if pod_status_phase != "Succeeded":
            pod_creation_timestamp = pod_info.metadata.creation_timestamp
            if pod_status.container_statuses:
                for container in pod_status.container_statuses:
                    pod_restart_count += container.restart_count
            if pod_status.init_container_statuses:
                for container in pod_status.init_container_statuses:
                    pod_restart_count += container.restart_count
            if pods_tracker[pod]:
                if pods_tracker[pod]["creation_timestamp"] != pod_creation_timestamp or \
                    pods_tracker[pod]["restart_count"] != pod_restart_count:
                    crashed_restarted_pods[namespace].append(pod)
                    pods_tracker[pod]["creation_timestamp"] = pod_creation_timestamp
                    pods_tracker[pod]["restart_count"] = pod_restart_count
            else:
                crashed_restarted_pods[namespace].append(pod)
                pods_tracker[pod]["creation_timestamp"] = pod_creation_timestamp
                pods_tracker[pod]["restart_count"] = pod_restart_count
    return crashed_restarted_pods


# Monitor the status of the pods in the specified namespace
# and set the status to true or false
def monitor_namespace(namespace):
    pods = list_pods(namespace)
    notready_pods = set()
    notready_containers = defaultdict(list)
    for pod in pods:
        pod_info = get_pod_status(pod, namespace)
        pod_status = pod_info.status
        pod_status_phase = pod_status.phase
        if pod_status_phase != "Running" and pod_status_phase != "Succeeded":
            notready_pods.add(pod)
        if pod_status_phase != "Succeeded":
            if pod_status.conditions:
                for condition in pod_status.conditions:
                    if condition.type == "Ready" and condition.status == "False":
                        notready_pods.add(pod)
                    if condition.type == "ContainersReady" and condition.status == "False":
                        if pod_status.container_statuses:
                            for container in pod_status.container_statuses:
                                if not container.ready:
                                    notready_containers[pod].append(container.name)
                        if pod_status.init_container_statuses:
                            for container in pod_status.init_container_statuses:
                                if not container.ready:
                                    notready_containers[pod].append(container.name)
    notready_pods = list(notready_pods)
    if len(notready_pods) != 0 or len(notready_containers) != 0:
        status = False
    else:
        status = True
    return status, notready_pods, notready_containers


# Get cluster operators and return yaml
def get_cluster_operators():
    operators_status = runcommand.invoke("kubectl get co -o yaml")
    status_yaml = yaml.load(operators_status, Loader=yaml.FullLoader)
    return status_yaml


# Monitor cluster operators
def monitor_cluster_operator(cluster_operators):
    failed_operators = []
    for operator in cluster_operators['items']:
        # loop through the conditions in the status section to find the dedgraded condition
        if "status" in operator.keys() and "conditions" in operator['status'].keys():
            for status_cond in operator['status']['conditions']:
                # if the degraded status is not false, add it to the failed operators to return
                if status_cond['type'] == "Degraded" and status_cond['status'] != "False":
                    failed_operators.append(operator['metadata']['name'])
                    break
        else:
            logging.info("Can't find status of " + operator['metadata']['name'])
            failed_operators.append(operator['metadata']['name'])
    # if failed operators is not 0, return a failure
    # else return pass
    if len(failed_operators) != 0:
        status = False
    else:
        status = True
    return status, failed_operators


# This will get the taint information for each of the master nodes
def get_taint_from_describe(node_name):
    # Will return the taints for the master nodes
    node_taint = runcommand.invoke("kubectl describe nodes/" + node_name + ' | grep Taints')
    # Need to get the taint type and take out any extra spaces
    taint_info = node_taint.split(':')[-1].replace(" ", '')
    return taint_info


# See if url is available
def is_url_available(url):
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        return False
    else:
        return True
