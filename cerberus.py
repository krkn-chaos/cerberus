#!/usr/bin/env python

import sys, os, time, datetime
import configparser, optparse
import requests
import _thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
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
        print("Exception when calling CoreV1Api->list_node: %s\n" % e)
    for node in ret.items:
        nodes.append(node.metadata.name)
    return nodes

# List pods in the given namespace
def list_pods(namespace):
    pods = []
    try:
        ret = cli.list_namespaced_pod(namespace, pretty=True)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)
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
            print("Exception when calling CoreV1Api->read_node_status: %s\n" % e)
        node_status = node_info.status.conditions[-1].status
        if node_status == "True":
            ready_nodes.append(node)
        else:
            notready_nodes.append(node)
    if len(notready_nodes) != 0:
       status = False
    else:
       status = True
    return status

# Monitor the status of the etcd and set the status to true or false
def monitor_etcd(etcd_namespace):
    etcd_pods = list_pods(etcd_namespace)
    etcd_ready_pods = []
    etcd_notready_pods = []
    for pod in etcd_pods:
        try:
            etcd_pod_info = cli.read_namespaced_pod_status(pod, etcd_namespace, pretty=True)
        except ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_pod_status: %s\n" % e)
        etcd_pod_status = etcd_pod_info.status.phase
        if etcd_pod_status == "Running":
           etcd_ready_pods.append(pod)
        else:
           etcd_notready_pods.append(pod)
    if len(etcd_notready_pods) != 0:
       status = False
    else:
       status = True
    return status

# Monitor the status of the openshift-apiserer and set the status to true or false
def monitor_openshift_apiserver(openshift_apiserver_namespace):
    openshift_apiserver_pods = list_pods(openshift_apiserver_namespace)
    apiserver_ready_pods = []
    apiserver_notready_pods = []
    for pod in openshift_apiserver_pods:
        apiserver_pod_info = cli.read_namespaced_pod_status(pod, openshift_apiserver_namespace, pretty=True)
        apiserver_pod_status = apiserver_pod_info.status.phase
        if apiserver_pod_status == "Running":
            apiserver_ready_pods.append(pod)
        else:
            apiserver_notready_pods.append(pod)
    if len(apiserver_notready_pods) != 0:
        status = False
    else:
        status = True
    return status

# Start a simple http server to publish the cerberus status file content
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        f = open('/tmp/cerberus_status','rb')
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
        cerberus_publish_status = config.get('cerberus', 'cerberus_publish_status')
        watch_etcd = config.get('cerberus', 'watch_etcd')
        etcd_namespace = config.get('cerberus', 'etcd_namespace')
        watch_openshift_apiserver = config.get('cerberus', 'watch_openshift_apiserver')
        openshift_apiserver_namespace = config.get('cerberus', 'openshift_apiserver_namespace')
        iterations = config.get('tunings', 'iterations')
        sleep_time = config.get('tunings', 'sleep_time')
        daemon_mode = config.get('tunings', 'daemon_mode')
       
        # run http server using a separate thread if cerberus is asked to publish the status. It is served by the http server.
        if cerberus_publish_status == "True":
            print("Publishing cerberus status at http://localhost:8086")
            _thread.start_new_thread(start_server, ())
        
        # Initialize the start iteration to 0 
        iteration = 0

        # Set the number of iterations to loop to infinity if daemon mode is enabled or else set it to the provided iterations count in the config
        if daemon_mode == "True":
            print("Daemon Mode enabled, cerberus will monitor forever")
            print("Ignoring the iterations set")
            iterations = float('inf')
        else:
            iterations = int(iterations)

        # Loop to run the components status checks starts here
        while ( int(iteration) < iterations ):
            iteration +=1
            
            # Monitor nodes status
            if watch_nodes == "True":
                watch_nodes_status = monitor_nodes()
                print("Iteration %s: Node status: %s" %(iteration, watch_nodes_status))
                print ("Sleeping for the specified duration: %s" %(sleep_time))
                time.sleep(float(sleep_time))
            else:
                print("Cerberus is not monitoring nodes, so setting the status to True and assuming that the nodes are ready")
                watch_nodes_status = True

            # Monitor etcd status
            if watch_etcd == "True":
                watch_etcd_status = monitor_etcd(etcd_namespace)
                print("Iteration %s: ETCD member pods status: %s" %(iteration, watch_etcd_status))
                print ("Sleeping for the specified duration: %s" %(sleep_time))
                time.sleep(float(sleep_time))
            else:
                print("Cerberus is not monitoring ETCD, so setting the status to True and assuming that the ETCD member pods are ready")
                watch_etcd_status = True

            # Monitor openshift-apiserver status
            if watch_openshift_apiserver == "True":
                watch_openshift_apiserver_status = monitor_openshift_apiserver(openshift_apiserver_namespace)
                print("Iteration %s: OpenShift apiserver status: %s" %(iteration, watch_openshift_apiserver_status))
                print ("Sleeping for the specified duration: %s" %(sleep_time))
                time.sleep(float(sleep_time))
            else:
                print("Cerberus is not monitoring openshift-apiserver, so setting the status to True and assuming that the openshift-apiserver is up and running")
                watch_openshift_apiserver_status = True
            
            # Set the cerberus status by checking the status of the watched components/resources for the http server to publish it
            if ( watch_nodes_status == True and watch_etcd_status == True and watch_openshift_apiserver_status == True):
                cerberus_status = True
            else:
                cerberus_status = False
            if cerberus_publish_status == "True":
               publish_cerberus_status(cerberus_status)
        else:
            print("Completed watching for the specified number of iterations: %s" %(iterations))
    else:
        print ("Could not find a config at %s, please check"%(cfg))
        sys.exit(1)

if __name__ == "__main__":
    # Initialize the parser to read the config
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", dest="cfg", help="config location")
    (options, args) = parser.parse_args()
    if (options.cfg is None):
        print ("Please check if you have passed the config")
        sys.exit(1)
    else:
        main(options.cfg)
