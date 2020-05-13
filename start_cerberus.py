#!/usr/bin/env python

import os
import sys
import time
import yaml
import logging
import optparse
import pyfiglet
import cerberus.server.server as server
import cerberus.inspect.inspect as inspect
import cerberus.invoke.command as runcommand
import cerberus.kubernetes.client as kubecli
import cerberus.slack.slack_client as slackcli


# Publish the cerberus status
def publish_cerberus_status(status):
    with open('/tmp/cerberus_status', 'w+') as file:
        file.write(str(status))


# Main function
def main(cfg):
    # Start cerberus
    print(pyfiglet.figlet_format("cerberus"))
    logging.info("Starting ceberus")

    # Parse and read the config
    if os.path.isfile(cfg):
        with open(cfg, 'r') as f:
            config = yaml.full_load(f)
        watch_nodes = config["cerberus"]["watch_nodes"]
        watch_cluster_operators = config["cerberus"].get("watch_cluster_operators", True)
        cerberus_publish_status = config["cerberus"]["cerberus_publish_status"]
        watch_namespaces = config["cerberus"]["watch_namespaces"]
        kubeconfig_path = config["cerberus"]["kubeconfig_path"]
        inspect_components = config["cerberus"]["inspect_components"]
        slack_integration = config["cerberus"]["slack_integration"]
        iterations = config["tunings"]["iterations"]
        sleep_time = config["tunings"]["sleep_time"]
        daemon_mode = config["tunings"]["daemon_mode"]

        # Initialize clients
        if not os.path.isfile(kubeconfig_path):
            kubeconfig_path = None
        logging.info("Initializing client to talk to the Kubernetes cluster")
        kubecli.initialize_clients(kubeconfig_path)

        if "openshift-sdn" in watch_namespaces:
            sdn_namespace = kubecli.check_sdn_namespace()
            watch_namespaces = [w.replace('openshift-sdn', sdn_namespace) for w in watch_namespaces]

        # Cluster info
        logging.info("Fetching cluster info")
        cluster_version = runcommand.invoke("kubectl get clusterversion")
        cluster_info = runcommand.invoke("kubectl cluster-info | awk 'NR==1' | sed -r "
                                         "'s/\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]//g'") # noqa
        logging.info("\n%s%s" % (cluster_version, cluster_info))

        # Run http server using a separate thread if cerberus is asked
        # to publish the status. It is served by the http server.
        if cerberus_publish_status:
            address = ("0.0.0.0", 8080)
            server_address = address[0]
            port = address[1]
            logging.info("Publishing cerberus status at http://%s:%s"
                         % (server_address, port))
            server.start_server(address)

        # Create slack WebCleint when slack intergation has been enabled
        if slack_integration:
            slack_integration = slackcli.initialize_slack_client()

        if inspect_components:
            logging.info("Detailed inspection of failed components has been enabled")
            inspect.delete_inspect_directory()

        # Initialize the start iteration to 0
        iteration = 0

        # Set the number of iterations to loop to infinity if daemon mode is
        # enabled or else set it to the provided iterations count in the config
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

            if slack_integration:
                weekday = runcommand.invoke("date '+%A'")[:-1]
                cop_slack_member_ID = config["cerberus"]["cop_slack_ID"][weekday]
                slack_team_alias = config["cerberus"]["slack_team_alias"]
                slackcli.slack_tagging(cop_slack_member_ID, slack_team_alias)

                if iteration == 1:
                    slackcli.slack_report_cerberus_start(cluster_info, weekday, cop_slack_member_ID)

            # Monitor nodes status
            if watch_nodes:
                watch_nodes_status, failed_nodes = kubecli.monitor_nodes()
                logging.info("Iteration %s: Node status: %s"
                             % (iteration, watch_nodes_status))
            else:
                logging.info("Cerberus is not monitoring nodes, so setting the status "
                             "to True and assuming that the nodes are ready")
                watch_nodes_status = True

            # Monitor cluster operators status
            if watch_cluster_operators:
                status_yaml = kubecli.get_cluster_operators()
                watch_cluster_operators_status, failed_operators = \
                    kubecli.monitor_cluster_operator( status_yaml)
                logging.info("Iteration %s: Cluster Operator status: %s"
                             % (iteration, watch_cluster_operators_status))
            else:
                logging.info("Cerberus is not monitoring cluster operators, "
                             "so setting the status to True and "
                             "assuming that the cluster operators are ready")
                watch_cluster_operators_status = True

            # Monitor each component in the namespace
            failed_pods_components = {}
            failed_pod_containers = {}
            watch_namespaces_status = True

            for namespace in watch_namespaces:
                watch_component_status, failed_component_pods, failed_containers = \
                    kubecli.monitor_component(iteration, namespace)
                watch_namespaces_status = watch_namespaces_status and watch_component_status
                if not watch_component_status:
                    failed_pods_components[namespace] = failed_component_pods
                    failed_pod_containers[namespace] = failed_containers

            # Check for the number of hits
            if cerberus_publish_status:
                logging.info("HTTP requests served: %s \n"
                             % (server.SimpleHTTPRequestHandler.requests_served))

            # Logging the failed components
            if not watch_nodes_status:
                logging.info("Failed nodes")
                logging.info("%s" % (failed_nodes))

            if not watch_cluster_operators_status:
                logging.info("Failed operators")
                logging.info(failed_operators)

            if not watch_nodes_status or not watch_namespaces_status:
                if not watch_namespaces_status:
                    logging.info("Failed pods and components")
                    for namespace, failures in failed_pods_components.items():
                        logging.info("%s: %s", namespace, failures)
                        for pod, containers in failed_pod_containers[namespace].items():
                            logging.info("Failed containers in %s: %s", pod, containers)

                if slack_integration:
                    slackcli.slack_logging(cluster_info, iteration, watch_nodes_status,
                                           watch_namespaces_status, failed_nodes,
                                           failed_pods_components)

            if inspect_components:
                inspect.inspect_components(failed_pods_components)

            cerberus_status = watch_nodes_status and watch_namespaces_status \
                and watch_cluster_operators_status

            if cerberus_publish_status:
                publish_cerberus_status(cerberus_status)

            # Sleep for the specified duration
            logging.info("Sleeping for the specified duration: %s" % (sleep_time))
            time.sleep(float(sleep_time))

        else:
            logging.info("Completed watching for the specified number of iterations: %s"
                         % (iterations))
    else:
        logging.error("Could not find a config at %s, please check" % (cfg))
        sys.exit(1)


if __name__ == "__main__":
    # Initialize the parser to read the config
    parser = optparse.OptionParser()
    parser.add_option(
        "-c", "--config",
        dest="cfg",
        help="config location",
        default="config/config.yaml",
    )
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
