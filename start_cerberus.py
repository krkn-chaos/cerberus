#!/usr/bin/env python

import sys
import os
import time
import optparse
import logging
import yaml
import cerberus.kubernetes.client as kubecli
import cerberus.invoke.command as runcommand
import cerberus.server.server as server


# Publish the cerberus status
def publish_cerberus_status(status):
    with open('/tmp/cerberus_status', 'w+') as file:
        file.write(str(status))


# Main function
def main(cfg):
    # Start cerberus
    logging.info("Starting ceberus")

    # Parse and read the config
    if os.path.isfile(cfg):
        with open(cfg, 'r') as f:
            config = yaml.full_load(f)
        watch_nodes = config["cerberus"]["watch_nodes"]
        cerberus_publish_status = \
            config["cerberus"]["cerberus_publish_status"]
        watch_namespaces = config["cerberus"]["watch_namespaces"]
        kubeconfig_path = config["cerberus"]["kubeconfig_path"]
        iterations = config["tunings"]["iterations"]
        sleep_time = config["tunings"]["sleep_time"]
        daemon_mode = config["tunings"]["daemon_mode"]

        # Initialize clients
        if not os.path.isfile(kubeconfig_path):
            kubeconfig_path = None
        logging.info("Initializing client to talk to the Kubernetes cluster")
        kubecli.initialize_clients(kubeconfig_path)

        # Cluster info
        logging.info("Fetching cluster info")
        cluster_version = runcommand.invoke("kubectl get clusterversion")
        cluster_info = runcommand.invoke("kubectl cluster-info | awk 'NR==1'")
        print("%s %s" % (cluster_version, cluster_info))

        # Run http server using a separate thread
        # if cerberus is asked to publish the status.
        # It is served by the http server.
        if cerberus_publish_status:
            address = ("0.0.0.0", 8080)
            server_address = address[0]
            port = address[1]
            logging.info("Publishing cerberus status at http://%s:%s"
                         % (server_address, port))
            server.start_server(address)

        # Initialize the start iteration to 0
        iteration = 0

        # Set the number of iterations to loop to infinity
        # if daemon mode is enabled
        # or else set it to the provided iterations count in the config
        if daemon_mode:
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
            if watch_nodes:
                watch_nodes_status, failed_nodes = kubecli.monitor_nodes()
                logging.info("Iteration %s: Node status: %s"
                             % (iteration, watch_nodes_status))
            else:
                logging.info("Cerberus is not monitoring nodes, "
                             "so setting the status to True and "
                             "assuming that the nodes are ready")
                watch_nodes_status = True

            # Monitor each component in the namespace
            # Set the initial cerberus_status
            failed_pods_components = {}
            cerberus_status = True

            for namespace in watch_namespaces:
                watch_component_status, failed_component_pods = \
                    kubecli.monitor_component(iteration, namespace)
                cerberus_status = cerberus_status and watch_component_status
                if not watch_component_status:
                    failed_pods_components[namespace] = failed_component_pods

            # Check for the number of hits
            if cerberus_publish_status:
                logging.info("HTTP requests served: %s "
                             %
                             (server.SimpleHTTPRequestHandler.requests_served))

            # Sleep for the specified duration
            logging.info("Sleeping for the "
                         "specified duration: %s" % (sleep_time))
            time.sleep(float(sleep_time))

            # Logging the failed components
            if not watch_nodes_status:
                logging.info("Failed nodes: %s \n" % (failed_nodes))

            if not cerberus_status:
                logging.info("Failed pods and components")
                for namespace, failures in failed_pods_components.items():
                    logging.info("%s: %s", namespace, failures)

            if cerberus_publish_status:
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
