import logging
from collections import defaultdict
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import cerberus.invoke.command as runcommand
import yaml

# Load kubeconfig and initialize kubernetes python client
def initialize_clients(kubeconfig_path):
    global cli
    config.load_kube_config(kubeconfig_path)
    cli = client.CoreV1Api()


# List nodes in the cluster
def list_nodes():
    nodes = []
    try:
        ret = cli.list_node(pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)
    for node in ret.items:
        nodes.append(node.metadata.name)
    return nodes


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


# Monitor the status of the cluster nodes and set the status to true or false
def monitor_nodes():
    nodes = list_nodes()
    notready_nodes = []
    node_kerneldeadlock_status = "False"
    for node in nodes:
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
        if (
            node_kerneldeadlock_status != "False"        # noqa
            or node_ready_status != "True"               # noqa
        ):
            notready_nodes.append(node)
    if len(notready_nodes) != 0:
        status = False
    else:
        status = True
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


# Monitor the status of the pods in the specified namespace
# and set the status to true or false
def monitor_namespace(namespace):
    pods = list_pods(namespace)
    notready_pods = set()
    notready_containers = defaultdict(list)
    for pod in pods:
        try:
            pod_info = cli.read_namespaced_pod_status(pod, namespace,
                                                      pretty=True)
        except ApiException as e:
            logging.error("Exception when calling \
                           CoreV1Api->read_namespaced_pod_status: %s\n" % e)
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


# Monitor component namespace
def monitor_component(iteration, component_namespace):
    watch_component_status, failed_component_pods, failed_containers = \
        monitor_namespace(component_namespace)
    logging.info("Iteration %s: %s: %s"
                 % (iteration, component_namespace, watch_component_status))
    return watch_component_status, failed_component_pods, failed_containers


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
        for status_cond in operator['status']['conditions']:
            if status_cond['type'] == "Degraded":
                # if the degraded status is not false, add it to the failed operators to return
                if status_cond['status'] != "False":
                    failed_operators.append(operator['metadata']['name'])
                break

    # if failed operators is not 0, return a failure
    # else return pass
    if len(failed_operators) != 0:
        status = False
    else:
        status = True

    return status, failed_operators
