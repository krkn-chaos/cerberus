#!/usr/bin/env python

import sys
import os
import time
import configparser
import optparse
import requests
import _thread
import logging
from kubernetes.client.rest import ApiException
from http.server import HTTPServer, BaseHTTPRequestHandler
from kubernetes import client, config
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Load kubeconfig and initialize kubernetes python client
config.load_kube_config()
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
    ready_nodes = []
    notready_nodes = []
    for node in nodes:
        try:
            node_info = cli.read_node_status(node, pretty=True)
        except ApiException as e:
            logging.error("Exception when calling \
                           CoreV1Api->read_node_status: %s\n" % e)
        node_status = node_info.status.conditions[-1].status
        if node_status == "True":
            ready_nodes.append(node)
        else:
            notready_nodes.append(node)
    if len(notready_nodes) != 0:
        status = False
    else:
        status = True
    return status, notready_nodes


# Monitor the status of the pods in the specified namespace
# and set the status to true or false
def monitor_namespace(namespace):
    pods = list_pods(namespace)
    ready_pods = []
    completed_pods = []
    notready_pods = []
    for pod in pods:
        try:
            pod_info = cli.read_namespaced_pod_status(pod, namespace,
                                                      pretty=True)
        except ApiException as e:
            logging.error("Exception when calling \
                           CoreV1Api->read_namespaced_pod_status: %s\n" % e)
        pod_status = pod_info.status.phase
        if pod_status == "Running":
            ready_pods.append(pod)
        elif (pod_status == "Completed" or pod_status == "Succeeded"):
            completed_pods.append(pod)
        else:
            notready_pods.append(pod)
    if len(notready_pods) != 0:
        status = False
    else:
        status = True
    return status, notready_pods


# Start a simple http server to publish the cerberus status file content
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        f = open('/tmp/cerberus_status', 'rb')
        self.wfile.write(f.read())


def start_server():
    httpd = HTTPServer(('localhost', 8086), SimpleHTTPRequestHandler)
    httpd.serve_forever()


# Publish the cerberus status
def publish_cerberus_status(status):
    with open('/tmp/cerberus_status', 'w+') as file:
        file.write(str(status))


# Main function
def main(cfg):
    # Parse and read the config
    if os.path.isfile(cfg):
        config = configparser.ConfigParser()
        config.read(cfg)
        watch_nodes = config.get('cerberus', 'watch_nodes')
        cerberus_publish_status = config.get('cerberus',
                                             'cerberus_publish_status')
        watch_etcd = config.get('cerberus', 'watch_etcd')
        etcd_namespace = config.get('cerberus', 'etcd_namespace')
        watch_openshift_apiserver = config.get('cerberus',
                                               'watch_openshift_apiserver')
        openshift_apiserver_namespace = \
            config.get('cerberus', 'openshift_apiserver_namespace')
        watch_kube_apiserver = config.get('cerberus', 'watch_kube_apiserver')
        kube_apiserver_namespace = config.get('cerberus',
                                              'kube_apiserver_namespace')
        watch_monitoring_stack = config.get('cerberus',
                                            'watch_monitoring_stack')
        monitoring_stack_namespace = config.get('cerberus',
                                                'monitoring_stack_namespace')
        watch_kube_controller = config.get('cerberus',
                                           'watch_kube_controller')
        kube_controller_namespace = config.get('cerberus',
                                               'kube_controller_namespace')
        iterations = config.get('tunings', 'iterations')
        sleep_time = config.get('tunings', 'sleep_time')
        daemon_mode = config.get('tunings', 'daemon_mode')

        # Start cerberus
        logging.info("Starting cerberus")

        # Run http server using a separate thread
        # if cerberus is asked to publish the status.
        # It is served by the http server.
        if cerberus_publish_status == "True":
            logging.info("Publishing cerberus status at http://localhost:8086")
            _thread.start_new_thread(start_server, ())

        # Initialize the start iteration to 0
        iteration = 0

        # Set the number of iterations to loop to infinity
        # if daemon mode is enabled
        # or else set it to the provided iterations count in the config
        if daemon_mode == "True":
            logging.info("Daemon mode enabled, cerberus will monitor forever")
            logging.info("Ignoring the iterations set")
            iterations = float('inf')
        else:
            iterations = int(iterations)

        # Loop to run the components status checks starts here
        while (int(iteration) < iterations):
            iteration += 1
            print("\n")

            # Monitor nodes status
            if watch_nodes == "True":
                watch_nodes_status, failed_nodes = monitor_nodes()
                logging.info("Iteration %s: Node status: %s"
                             % (iteration, watch_nodes_status))
            else:
                logging.info("Cerberus is not monitoring nodes, "
                             "so setting the status to True and "
                             "assuming that the nodes are ready")
                watch_nodes_status = True

            # Monitor etcd status
            if watch_etcd == "True":
                watch_etcd_status, failed_etcd_pods = \
                    monitor_namespace(etcd_namespace)
                logging.info("Iteration %s: Etcd member pods status: %s"
                             % (iteration, watch_etcd_status))
            else:
                logging.info("Cerberus is not monitoring ETCD, "
                             "so setting the status to True and "
                             "assuming that the ETCD member pods are ready")
                watch_etcd_status = True

            # Monitor openshift-apiserver status
            if watch_openshift_apiserver == "True":
                watch_openshift_apiserver_status, failed_ocp_apiserver_pods = \
                    monitor_namespace(openshift_apiserver_namespace)
                logging.info("Iteration %s: OpenShift apiserver status: %s"
                             % (iteration, watch_openshift_apiserver_status))
            else:
                logging.info("Cerberus is not monitoring openshift-apiserver, "
                             "so setting the status to True "
                             "and assuming that the "
                             "openshift-apiserver is up and running")
                watch_openshift_apiserver_status = True

            # Monitor kube apiserver status
            if watch_kube_apiserver == "True":
                watch_kube_apiserver_status, failed_kube_apiserver_pods = \
                    monitor_namespace(kube_apiserver_namespace)
                logging.info("Iteration %s: Kube ApiServer status: %s"
                             % (iteration, watch_kube_apiserver_status))
            else:
                logging.info("Cerberus is not monitoring Kube ApiServer, so "
                             "setting the status to True and assuming that "
                             "the Kube ApiServer is up and running")
                watch_kube_apiserver_status = True

            # Monitor prometheus/monitoring stack
            if watch_monitoring_stack == "True":
                watch_monitoring_stack_status, failed_monitoring_stack = \
                    monitor_namespace(monitoring_stack_namespace)
                logging.info("Iteration %s: Monitoring stack status: %s"
                             % (iteration, watch_monitoring_stack_status))
            else:
                logging.info("Cerberus is not monitoring prometheus stack, "
                             "so setting the status to True "
                             "and assuming that the monitoring stack is "
                             "up and running")
                watch_monitoring_stack_status = True

            # Monitor kube controller
            if watch_kube_controller == "True":
                watch_kube_controller_status, failed_kube_controller_pods = \
                    monitor_namespace(kube_controller_namespace)
                logging.info("Iteration %s: Kube controller status: %s"
                             % (iteration, watch_kube_controller_status))
            else:
                logging.info("Cerberus is not monitoring kube controller, so "
                             "setting the status to True and assuming that "
                             "the kube controller is up and running")
                watch_kube_controller_status = True

            # Sleep for the specified duration
            logging.info("Sleeping for the "
                         "specified duration: %s" % (sleep_time))
            time.sleep(float(sleep_time))

            # Set the cerberus status by checking the status of the
            # watched components/resources for the http server to publish it
            if watch_nodes_status and watch_etcd_status \
                and watch_openshift_apiserver_status \
                and watch_kube_apiserver \
                and watch_monitoring_stack_status \
                and watch_kube_controller:
                cerberus_status = True
            else:
                cerberus_status = False
                logging.info("Failed nodes: %s\n"
                             "Failed etcd pods: %s\n"
                             "Failed openshift apiserver pods: %s\n"
                             "Failed kube apiserver pods: %s\n"
                             "Failed monitoring stack components: %s\n"
                             "Failed kube controller pods: %s "
                             % (failed_nodes, failed_etcd_pods,
                                failed_ocp_apiserver_pods,
                                failed_kube_apiserver_pods,
                                failed_monitoring_stack,
                                failed_kube_controller_pods))

            if cerberus_publish_status == "True":
                publish_cerberus_status(cerberus_status)
        else:
            logging.info("Completed watching for the specified number of "
                         "iterations: %s" % (iterations))
    else:
        logging.error("Could not find a config at %s, please check" % (cfg))
        sys.exit(1)


if __name__ == "__main__":
    # Initialize the parser to read the config
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="cfg", help="config location")
    (options, args) = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("cerberus.report", mode='w'),
            logging.StreamHandler()
        ]
    )
    if (options.cfg is None):
        logging.error("Please check if you have passed the config")
        sys.exit(1)
    else:
        main(options.cfg)
