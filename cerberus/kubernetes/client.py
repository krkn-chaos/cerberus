import yaml
import logging
import requests
from collections import defaultdict
from kubernetes import client, config
import cerberus.invoke.command as runcommand
from kubernetes.client.rest import ApiException
from urllib3.exceptions import InsecureRequestWarning


pods_tracker = defaultdict(dict)


# Load kubeconfig and initialize kubernetes python client
def initialize_clients(kubeconfig_path):
    global cli
    config.load_kube_config(kubeconfig_path)
    cli = client.CoreV1Api()


# List nodes in the cluster
def list_nodes(label_selector=None):
    nodes = []
    try:
        if label_selector:
            ret = cli.list_node(pretty=True, label_selector=label_selector)
        else:
            ret = cli.list_node(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)
    for node in ret.items:
        nodes.append(node.metadata.name)
    return nodes


def get_node_info(node):
    try:
        return cli.read_node_status(node, pretty=True)
    except ApiException as e:
        logging.error("Exception when calling \
                       CoreV1Api->read_node_status: %s\n" % e)


# List pods in the given namespace
def list_pods(namespace):
    pods = []
    try:
        ret = cli.list_namespaced_pod(namespace, pretty=True)
    except ApiException as e:
        logging.error("Exception when calling \
                       CoreV1Api->list_namespaced_pod: %s\n" % e)
    for pod in ret.items:
        pods.append(pod.metadata.name)
    return pods


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
        node_info = get_node_info(node)
        for condition in node_info.status.conditions:
            if condition.type == "KernelDeadlock":
                node_kerneldeadlock_status = condition.status
            elif condition.type == "Ready":
                node_ready_status = condition.status
            else:
                continue
        if node_kerneldeadlock_status != "False" or node_ready_status != "True":
            notready_nodes.append(node)
    status = False if notready_nodes else True
    return status, notready_nodes


# Check the namespace name for default SDN
def check_sdn_namespace():
    for item in cli.list_namespace().items:
        if item.metadata.name == "openshift-ovn-kubernetes":
            return "openshift-ovn-kubernetes"
        elif item.metadata.name == "openshift-sdn":
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
    if notready_pods or notready_containers:
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
    # return False if there are failed operators else return True
    status = False if failed_operators else True
    return status, failed_operators


# Check for NoSchedule taint in all the master nodes
def check_master_taint(master_nodes):
    schedulable_masters = []
    for node in master_nodes:
        node_info = get_node_info(node)
        NoSchedule_taint = False
        try:
            for taint in node_info.spec.taints:
                if taint.key == "node-role.kubernetes.io/master" and taint.effect == "NoSchedule":
                    NoSchedule_taint = True
                    break
            if not NoSchedule_taint:
                schedulable_masters.append(node)
        except Exception:
            schedulable_masters.append(node)
    return schedulable_masters


# See if url is available
def is_url_available(url):
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        return False
    else:
        return True
