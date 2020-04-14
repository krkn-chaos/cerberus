#!/usr/bin/env python

import sys
import os
import time
import optparse
import logging
import yaml
import json
import cerberus.kubernetes.client as kubecli
import cerberus.slack.slack_client as slackcli
import cerberus.invoke.command as runcommand
import cerberus.server.server as server
import pyfiglet 

# Publish the cerberus status
def publish_cerberus_status(status):
    with open('/tmp/cerberus_status.json', 'w+') as file:
        json.dump({'cerberus_status': str(status)}, file)


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
        cerberus_publish_status = \
            config["cerberus"]["cerberus_publish_status"]
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

        # Cluster info
        logging.info("Fetching cluster info")
        cluster_version = runcommand.invoke("kubectl get clusterversion")
        cluster_info = runcommand.invoke("kubectl cluster-info | awk 'NR==1' | sed -r "
                                         "'s/\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]//g'") # noqa
        logging.info("\n%s%s" % (cluster_version, cluster_info))

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

        # Create slack WebCleint when slack intergation has been enabled
        if slack_integration:
            try:
                slackcli.initialize_slack_client()
            except Exception as e:
                slack_integration = False
                logging.error("Couldn't create slack WebClient. Check if slack env "
                              "varaibles are set. Exception: %s" % (e))
                logging.info("Slack integration has been disabled.")

        # Remove 'inspect_data' directory if it exists.
        # 'inspect_data' directory is used to collect
        # logs, events and metrics of the failed component
        if os.path.isdir("inspect_data/"):
            logging.info("Deleting existing inspect_data directory")
            runcommand.invoke("rm -R inspect_data")

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

            if slack_integration:
                weekday = runcommand.invoke("date '+%A'")[:-1]
                cop_slack_member_ID = config["cerberus"]['cop_slack_ID'][weekday]
                valid_cops = slackcli.get_channel_members()['members']

                if iteration == 1:
                    if cop_slack_member_ID in valid_cops:
                        slack_tag = "Hi <@" + cop_slack_member_ID + ">! The cop " \
                                    "for " + weekday + "!\n"
                    else:
                        slack_tag = "@here "
                    slackcli.post_message_in_slack(slack_tag + "Cerberus has started monitoring! "
                                                   ":skull_and_crossbones: %s" % (cluster_info))

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
                if slack_integration:
                    failed_namespaces = ", ".join(list(failed_pods_components.keys()))
                    valid_cops = slackcli.get_channel_members()['members']
                    cerberus_report_path = runcommand.invoke("pwd | tr -d '\n'")
                    if cop_slack_member_ID in valid_cops:
                        # If the cop assigned is a member of the slack channel, tag the cop
                        # while reporting every failure
                        slack_tag = "<@" + cop_slack_member_ID + ">"
                    else:
                        # If a cop isn't assigned for the day, tag everyone by using @here
                        # while reporting every failure
                        slack_tag = "@here"
                    slackcli.post_message_in_slack(slack_tag + " %sIn iteration %d, cerberus "
                                                   "found issues in namespaces: *%s*. Hence, "
                                                   "setting the go/no-go signal to false. The "
                                                   "full report is at *%s* on the host cerberus "
                                                   "is running."
                                                   % (cluster_info, iteration,
                                                      failed_namespaces, cerberus_report_path))

            if inspect_components:
                for namespace in failed_pods_components.keys():
                    dir_name = "inspect_data/" + namespace + "-logs"
                    if os.path.isdir(dir_name):
                        runcommand.invoke("rm -R " + dir_name)
                        logging.info("Deleted existing %s directory" % (dir_name))
                    command_out = runcommand.invoke("oc adm inspect ns/" + namespace + " --dest"
                                                    "-dir=" + dir_name)
                    logging.info(command_out)

            if cerberus_publish_status:
                publish_cerberus_status(cerberus_status)
        else:
            logging.info("Completed watching for the specified number of iterations: %s"
                         % (iterations))
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
