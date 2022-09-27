import re
import os
import sys
import yaml
import time
import logging
import requests
import urllib3
from collections import defaultdict
from kubernetes import client, config
import cerberus.invoke.command as runcommand
from kubernetes.client.rest import ApiException

pods_tracker = defaultdict(dict)

kubeconfig_path_global = ""


# Load kubeconfig and initialize kubernetes python client
def initialize_clients(kubeconfig_path, chunk_size, timeout):
    global cli
    global api_client
    global client_config
    global request_chunk_size
    global cmd_timeout
    global kubeconfig_path_global

    """Initialize object and create clients from specified kubeconfig"""
    client_config = client.Configuration()
    http_proxy = os.getenv("http_proxy", None)
    """Proxy has auth header"""
    if http_proxy and "@" in http_proxy:
        proxy_auth = http_proxy.split("@")[0].split("//")[1]
        user_pass = proxy_auth.split(":")[0]
        client_config.username = user_pass[0]
        client_config.password = user_pass[1]
    client_config.ssl_ca_cert = False
    client_config.verify_ssl = False
    config.load_kube_config(config_file=kubeconfig_path, persist_config=True, client_configuration=client_config)
    proxy_url = http_proxy
    if proxy_url:
        client_config.proxy = proxy_url
        if proxy_auth:
            client_config.proxy_headers = urllib3.util.make_headers(proxy_basic_auth=proxy_auth)

    client.Configuration.set_default(client_config)
    cli = client.CoreV1Api()
    cmd_timeout = timeout
    request_chunk_size = str(chunk_size)
    kubeconfig_path_global = kubeconfig_path
    logging.info("client set")


def list_continue_helper(func, *args, **keyword_args):
    ret_overall = []
    try:
        ret = func(*args, **keyword_args)
        ret_overall.append(ret)
        continue_string = ret.metadata._continue

        while continue_string:
            ret = func(*args, **keyword_args, _continue=continue_string)
            ret_overall.append(ret)
            continue_string = ret.metadata._continue

    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->%s: %s\n" % (str(func), e))

    return ret_overall


# List nodes in the cluster
def list_nodes(label_selector=None):
    nodes = []
    try:
        if label_selector:
            ret = list_continue_helper(
                cli.list_node, pretty=True, label_selector=label_selector, limit=request_chunk_size
            )
        else:
            ret = list_continue_helper(cli.list_node, pretty=True, limit=request_chunk_size)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)

    for ret_items in ret:
        for node in ret_items.items:
            nodes.append(node.metadata.name)

    return nodes


# List all namespaces
def list_namespaces():
    namespaces = []
    ret_overall = list_continue_helper(cli.list_namespace, pretty=True, limit=request_chunk_size)
    for ret_items in ret_overall:
        for namespace in ret_items.items:
            namespaces.append(namespace.metadata.name)
    return namespaces


# Monitor the status of all specified namespaces
# and set the status to true or false
def monitor_namespaces_status(watch_namespaces, watch_terminating_namespaces, iteration, iter_track_time):
    namespaces = []
    none_terminating = True
    if watch_terminating_namespaces:
        watch_nodes_start_time = time.time()
        try:
            ret = cli.list_namespace(pretty=True)
        except ApiException as e:
            logging.error("Exception when calling CoreV1Api->list_namespace: %s\n" % e)
            sys.exit(1)
        for namespace in ret.items:
            if namespace.metadata.name in watch_namespaces:
                if namespace.status.phase != "Active":
                    namespaces.append(namespace.metadata.name)
                    none_terminating = False
        iter_track_time["watch_terminating_namespaces"] = time.time() - watch_nodes_start_time
        logging.info("Iteration %s: No Terminating Namespaces status: %s" % (iteration, str(none_terminating)))
    else:
        logging.info(
            "Cerberus is not monitoring namespaces, so setting the status "
            "to True and assuming that the namespaces are Active"
        )
    return namespaces


# Get node status
def get_node_info(node):
    try:
        return cli.read_node_status(node)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->read_node_status: %s\n" % e)


# Get status of a pod in a namespace
def get_pod_status(pod, namespace):
    try:
        return cli.read_namespaced_pod_status(pod, namespace, pretty=True)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->read_namespaced_pod_status: %s\n" % e)


# Outputs a json blob with information about all the nodes
def get_all_nodes_info():
    try:
        return list_continue_helper(cli.list_node, limit=request_chunk_size)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_node: %s\n" % e)


# Outputs a json blob with informataion about all pods in a given namespace
def get_all_pod_info(namespace):
    try:
        ret = list_continue_helper(cli.list_namespaced_pod, namespace, pretty=True, limit=request_chunk_size)
    except ApiException as e:
        logging.error("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

    return ret


# Check if all the watch_namespaces are valid
def check_namespaces(namespaces):
    try:
        valid_namespaces = list_namespaces()
        regex_namespaces = set(namespaces) - set(valid_namespaces)
        final_namespaces = set(namespaces) - set(regex_namespaces)
        valid_regex = set()
        if regex_namespaces:
            for namespace in valid_namespaces:
                for regex_namespace in regex_namespaces:
                    if re.search(regex_namespace, namespace):
                        final_namespaces.add(namespace)
                        valid_regex.add(regex_namespace)
                        break
        invalid_namespaces = regex_namespaces - valid_regex
        if invalid_namespaces:
            raise Exception("There exists no namespaces matching: %s" % (invalid_namespaces))
        return list(final_namespaces)
    except Exception as e:
        logging.info("check namespaces error%s" % (e))
        sys.exit(1)


# Check the namespace name for default SDN
def check_sdn_namespace():
    namespaces = list_namespaces()
    if "openshift-ovn-kubernetes" in namespaces:
        return "openshift-ovn-kubernetes"
    if "openshift-sdn" in namespaces:
        return "openshift-sdn"
    logging.error(
        "Could not find openshift-sdn and openshift-ovn-kubernetes namespaces, "
        "please specify the correct networking namespace in config file"
    )
    sys.exit(1)


# Monitor the status of the cluster nodes and set the status to true or false
def monitor_nodes():
    notready_nodes = []
    all_nodes_info_list = get_all_nodes_info()
    for all_nodes_info in all_nodes_info_list:
        for node_info in all_nodes_info.items:
            node = node_info.metadata.name
            node_kerneldeadlock_status = "False"
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


def process_nodes(watch_nodes, iteration, iter_track_time):
    if watch_nodes:
        watch_nodes_start_time = time.time()
        watch_nodes_status, failed_nodes = monitor_nodes()
        iter_track_time["watch_nodes"] = time.time() - watch_nodes_start_time
        logging.info("Iteration %s: Node status: %s" % (iteration, watch_nodes_status))
    else:
        logging.info(
            "Cerberus is not monitoring nodes, so setting the status " "to True and assuming that the nodes are ready"
        )
        watch_nodes_status = True
        failed_nodes = []
    return watch_nodes_status, failed_nodes


# Track the pods that were crashed/restarted during the sleep interval of an iteration
def namespace_sleep_tracker(namespace, pods_tracker, ignore_patterns):
    crashed_restarted_pods = defaultdict(list)
    all_pod_info_list = get_all_pod_info(namespace)
    if all_pod_info_list is not None and len(all_pod_info_list) > 0:
        for all_pod_info in all_pod_info_list:
            for pod_info in all_pod_info.items:
                pod = pod_info.metadata.name
                pod_status = pod_info.status
                pod_status_phase = pod_status.phase
                pod_restart_count = 0
                match = False
                if ignore_patterns:
                    for pattern in ignore_patterns:
                        if re.match(pattern, pod):
                            match = True
                if match:
                    continue
                if pod_status_phase != "Succeeded":
                    pod_creation_timestamp = pod_info.metadata.creation_timestamp
                    if pod_status.container_statuses is not None:
                        for container in pod_status.container_statuses:
                            pod_restart_count += container.restart_count
                    if pod_status.init_container_statuses is not None:
                        for container in pod_status.init_container_statuses:
                            pod_restart_count += container.restart_count

                    if pod in pods_tracker:
                        if (
                            pods_tracker[pod]["creation_timestamp"] != pod_creation_timestamp
                            or pods_tracker[pod]["restart_count"] != pod_restart_count
                        ):
                            pod_restart_count = max(pod_restart_count, pods_tracker[pod]["restart_count"])
                            if pods_tracker[pod]["creation_timestamp"] != pod_creation_timestamp:
                                crashed_restarted_pods[namespace].append((pod, "crash"))
                            if pods_tracker[pod]["restart_count"] != pod_restart_count:
                                restarts = pod_restart_count - pods_tracker[pod]["restart_count"]
                                crashed_restarted_pods[namespace].append((pod, "restart", restarts))
                            pods_tracker[pod] = {
                                "creation_timestamp": pod_creation_timestamp,
                                "restart_count": pod_restart_count,
                            }
                    else:
                        crashed_restarted_pods[namespace].append((pod, "crash"))
                        if pod_restart_count != 0:
                            crashed_restarted_pods[namespace].append((pod, "restart", pod_restart_count))
                        pods_tracker[pod] = {
                            "creation_timestamp": pod_creation_timestamp,
                            "restart_count": pod_restart_count,
                        }
    return crashed_restarted_pods


# Monitor the status of the pods in the specified namespace
# and set the status to true or false
def monitor_namespace(namespace, ignore_pattern=None):
    notready_pods = set()
    match = False
    notready_containers = defaultdict(list)
    all_pod_info_list = get_all_pod_info(namespace)
    if all_pod_info_list is not None and len(all_pod_info_list) > 0:
        for all_pod_info in all_pod_info_list:
            for pod_info in all_pod_info.items:
                pod = pod_info.metadata.name
                if ignore_pattern:
                    for pattern in ignore_pattern:
                        if re.match(pattern, pod):
                            match = True
                if match:
                    continue
                pod_status = pod_info.status
                pod_status_phase = pod_status.phase
                if pod_status_phase != "Running" and pod_status_phase != "Succeeded":
                    notready_pods.add(pod)
                if pod_status_phase != "Succeeded":
                    if pod_status.conditions is not None:
                        for condition in pod_status.conditions:
                            if condition.type == "Ready" and condition.status == "False":
                                notready_pods.add(pod)
                            if condition.type == "ContainersReady" and condition.status == "False":
                                if pod_status.container_statuses is not None:
                                    for container in pod_status.container_statuses:
                                        if not container.ready:
                                            notready_containers[pod].append(container.name)
                                if pod_status.init_container_statuses is not None:
                                    for container in pod_status.init_container_statuses:
                                        if not container.ready:
                                            notready_containers[pod].append(container.name)
    notready_pods = list(notready_pods)
    if notready_pods or notready_containers:
        status = False
    else:
        status = True
    return status, notready_pods, notready_containers


def process_namespace(iteration, namespace, failed_pods_components, failed_pod_containers, ignore_pattern):
    watch_component_status, failed_component_pods, failed_containers = monitor_namespace(namespace, ignore_pattern)
    logging.info("Iteration %s: %s: %s" % (iteration, namespace, watch_component_status))
    if not watch_component_status:
        failed_pods_components[namespace] = failed_component_pods
        failed_pod_containers[namespace] = failed_containers


# Get cluster operators and return yaml
def get_cluster_operators():
    operators_status = runcommand.invoke("kubectl get co -o yaml --kubeconfig " + kubeconfig_path_global, cmd_timeout)
    status_yaml = yaml.load(operators_status, Loader=yaml.FullLoader)
    return status_yaml


# Monitor cluster operators
def monitor_cluster_operator(cluster_operators):
    failed_operators = []
    for operator in cluster_operators["items"]:
        # loop through the conditions in the status section to find the dedgraded condition
        if "status" in operator.keys() and "conditions" in operator["status"].keys():
            for status_cond in operator["status"]["conditions"]:
                # if the degraded status is not false, add it to the failed operators to return
                if status_cond["type"] == "Degraded" and status_cond["status"] != "False":
                    failed_operators.append(operator["metadata"]["name"])
                    break
        else:
            logging.info("Can't find status of " + operator["metadata"]["name"])
            failed_operators.append(operator["metadata"]["name"])
    # return False if there are failed operators else return True
    status = False if failed_operators else True
    return status, failed_operators


def process_cluster_operator(distribution, watch_cluster_operators, iteration, iter_track_time):
    if distribution == "openshift" and watch_cluster_operators:
        watch_co_start_time = time.time()
        status_yaml = get_cluster_operators()
        watch_cluster_operators_status, failed_operators = monitor_cluster_operator(status_yaml)
        iter_track_time["watch_cluster_operators"] = time.time() - watch_co_start_time
        logging.info("Iteration %s: Cluster Operator status: %s" % (iteration, watch_cluster_operators_status))
    else:
        watch_cluster_operators_status = True
        failed_operators = []
    return watch_cluster_operators_status, failed_operators


# Check for NoSchedule taint in all the master nodes
def check_master_taint(master_nodes, master_label):
    schedulable_masters = []

    for master_node in master_nodes:
        node_info = get_node_info(master_node)
        node = node_info.metadata.name
        NoSchedule_taint = False
        try:
            if node_info.spec is not None:
                if node_info.spec.taints is not None:
                    for taint in node_info.spec.taints:
                        if taint.key == str(master_label) and taint.effect == "NoSchedule":
                            NoSchedule_taint = True
                            break
                    if not NoSchedule_taint:
                        schedulable_masters.append(node)
        except Exception as e:
            logging.info("Exception getting master nodes" + str(e))
            schedulable_masters.append(node)
    return schedulable_masters


def process_master_taint(master_nodes, master_label, iteration, iter_track_time):
    schedulable_masters = []
    if len(master_nodes) > 0:
        if iteration % 10 == 1:
            check_taint_start_time = time.time()
            schedulable_masters = check_master_taint(master_nodes, master_label)
            iter_track_time["check_master_taint"] = time.time() - check_taint_start_time
    return schedulable_masters


# See if url is available
def is_url_available(url, header=None):
    try:
        response = requests.get(url, headers=header, verify=False)
        if response.status_code != 200:
            return False
        else:
            return True
    except Exception:
        return False


def process_routes(watch_url_routes, iter_track_time):
    failed_routes = []
    if watch_url_routes:
        watch_routes_start_time = time.time()
        for route_info in watch_url_routes:
            # Might need to get different authorization types here
            header = {"Accept": "application/json"}
            if len(route_info) > 1:
                header["Authorization"] = route_info[1]
            route_status = is_url_available(route_info[0], header)
            if not route_status:
                failed_routes.append(route_info[0])
        iter_track_time["watch_routes"] = time.time() - watch_routes_start_time
    return failed_routes


# Get CSR's in yaml format
def get_csrs():
    csr_string = runcommand.invoke("oc get csr -o yaml --kubeconfig " + kubeconfig_path_global, cmd_timeout)
    csr_yaml = yaml.load(csr_string, Loader=yaml.FullLoader)
    return csr_yaml


def get_host() -> str:
    """Returns the Kubernetes server URL"""
    return client.configuration.Configuration.get_default_copy().host


def get_clusterversion_string() -> str:
    """Returns clusterversion status text on OpenShift, empty string on other distributions"""
    try:
        custom_objects_api = client.CustomObjectsApi()
        cvs = custom_objects_api.list_cluster_custom_object(
            "config.openshift.io",
            "v1",
            "clusterversions",
        )
        for cv in cvs["items"]:
            for condition in cv["status"]["conditions"]:
                if condition["type"] == "Progressing":
                    return condition["message"]
        return ""
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return ""
        else:
            raise
