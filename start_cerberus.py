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
        watch_etcd = config["cerberus"]["watch_etcd"]
        etcd_namespace = config["cerberus"]["etcd_namespace"]
        watch_openshift_apiserver = \
            config["cerberus"]["watch_openshift_apiserver"]
        openshift_apiserver_namespace = \
            config["cerberus"]["openshift_apiserver_namespace"]
        watch_kube_apiserver = config["cerberus"]["watch_kube_apiserver"]
        kube_apiserver_namespace = \
            config["cerberus"]["kube_apiserver_namespace"]
        watch_monitoring_stack = config["cerberus"]["watch_monitoring_stack"]
        monitoring_stack_namespace = \
            config["cerberus"]["monitoring_stack_namespace"]
        watch_kube_controller = config["cerberus"]["watch_kube_controller"]
        kube_controller_namespace = \
            config["cerberus"]["kube_controller_namespace"]
        watch_machine_api = config["cerberus"]["watch_machine_api_components"]
        machine_api_namespace = config["cerberus"]["machine_api_namespace"]
        watch_kube_scheduler = config["cerberus"]["watch_kube_scheduler"]
        kube_scheduler_namespace = \
            config["cerberus"]["kube_scheduler_namespace"]
        watch_openshift_ingress = config["cerberus"]["watch_openshift_ingress"]
        openshift_ingress_namespace = \
            config["cerberus"]["openshift_ingress_namespace"]
        watch_openshift_sdn = config["cerberus"]["watch_openshift_sdn"]
        openshift_sdn_namespace = config["cerberus"]["openshift_sdn_namespace"]
        watch_ovnkubernetes = config["cerberus"]["watch_ovnkubernetes"]
        ovn_namespace = config["cerberus"]["ovn_namespace"]
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

            # Monitor etcd status
            if watch_etcd:
                watch_etcd_status, failed_etcd_pods = \
                    kubecli.monitor_namespace(etcd_namespace)
                logging.info("Iteration %s: Etcd member pods status: %s"
                             % (iteration, watch_etcd_status))
            else:
                logging.info("Cerberus is not monitoring ETCD, "
                             "so setting the status to True and "
                             "assuming that the ETCD member pods are ready")
                watch_etcd_status = True

            # Monitor openshift-apiserver status
            if watch_openshift_apiserver:
                watch_openshift_apiserver_status, failed_ocp_apiserver_pods = \
                    kubecli.monitor_namespace(openshift_apiserver_namespace)
                logging.info("Iteration %s: OpenShift apiserver status: %s"
                             % (iteration, watch_openshift_apiserver_status))
            else:
                logging.info("Cerberus is not monitoring openshift-apiserver, "
                             "so setting the status to True "
                             "and assuming that the "
                             "openshift-apiserver is up and running")
                watch_openshift_apiserver_status = True

            # Monitor kube apiserver status
            if watch_kube_apiserver:
                watch_kube_apiserver_status, failed_kube_apiserver_pods = \
                    kubecli.monitor_namespace(kube_apiserver_namespace)
                logging.info("Iteration %s: Kube ApiServer status: %s"
                             % (iteration, watch_kube_apiserver_status))
            else:
                logging.info("Cerberus is not monitoring Kube ApiServer, so "
                             "setting the status to True and assuming that "
                             "the Kube ApiServer is up and running")
                watch_kube_apiserver_status = True

            # Monitor prometheus/monitoring stack
            if watch_monitoring_stack:
                watch_monitoring_stack_status, failed_monitoring_stack = \
                    kubecli.monitor_namespace(monitoring_stack_namespace)
                logging.info("Iteration %s: Monitoring stack status: %s"
                             % (iteration, watch_monitoring_stack_status))
            else:
                logging.info("Cerberus is not monitoring prometheus stack, "
                             "so setting the status to True "
                             "and assuming that the monitoring stack is "
                             "up and running")
                watch_monitoring_stack_status = True

            # Monitor kube controller
            if watch_kube_controller:
                watch_kube_controller_status, failed_kube_controller_pods = \
                    kubecli.monitor_namespace(kube_controller_namespace)
                logging.info("Iteration %s: Kube controller status: %s"
                             % (iteration, watch_kube_controller_status))
            else:
                logging.info("Cerberus is not monitoring kube controller, so "
                             "setting the status to True and assuming that "
                             "the kube controller is up and running")
                watch_kube_controller_status = True

            # Monitor machine api components
            # Components includes operator, controller and auto scaler
            if watch_machine_api:
                watch_machine_api_status, failed_machine_api_components = \
                    kubecli.monitor_namespace(machine_api_namespace)
                logging.info("Iteration %s: Machine API components status: %s"
                             % (iteration, watch_machine_api_status))
            else:
                logging.info("Cerberus is not monitoring machine api "
                             "components, so setting the status to True and "
                             "assuming that it is up and running")
                watch_machine_api_status = True

            # Monitor kube scheduler
            if watch_kube_scheduler:
                watch_kube_scheduler_status, failed_kube_scheduler_pods = \
                    kubecli.monitor_namespace(kube_scheduler_namespace)
                logging.info("Iteration %s: Kube scheduler status: %s"
                             % (iteration, watch_kube_scheduler_status))
            else:
                logging.info("Cerberus is not monitoring kube scheduler, so "
                             "setting the status to True and assuming that "
                             "the kube scheduler is up and running")
                watch_kube_scheduler_status = True

            # Monitor openshift-ingress status
            if watch_openshift_ingress:
                watch_openshift_ingress_status, failed_ocp_ingress_pods = \
                    kubecli.monitor_namespace(openshift_ingress_namespace)
                logging.info("Iteration %s: OpenShift ingress status: %s"
                             % (iteration, watch_openshift_ingress_status))
            else:
                logging.info("Cerberus is not monitoring openshift-ingress, "
                             "so setting the status to True "
                             "and assuming that the "
                             "openshift-ingress is up and running")
                watch_openshift_ingress_status = True

            # Monitor openshift-sdn status
            if watch_openshift_sdn:
                watch_openshift_sdn_status, failed_ocp_sdn_pods = \
                    kubecli.monitor_namespace(openshift_sdn_namespace)
                logging.info("Iteration %s: OpenShift SDN status: %s"
                             % (iteration, watch_openshift_sdn_status))
            else:
                logging.info("Cerberus is not monitoring openshift-sdn, "
                             "assuming it is up and running")
                watch_openshift_sdn_status = True

            # Monitor openshift-ovn-kubernetes status
            if watch_ovnkubernetes:
                watch_ovnkubernetes_status, failed_ovnkubernetes_pods = \
                    kubecli.monitor_namespace(ovn_namespace)
                logging.info("Iteration %s: OpenShift OVN status: %s"
                             % (iteration, watch_ovnkubernetes_status))
            else:
                logging.info("Cerberus is not monitoring "
                             "openshift-ovn-kubernetes, "
                             "assuming it is up and running")
                watch_ovnkubernetes_status = True

            # Check for the number of hits
            if cerberus_publish_status:
                logging.info("HTTP requests served: %s "
                             %
                             (server.SimpleHTTPRequestHandler.requests_served))

            # Sleep for the specified duration
            logging.info("Sleeping for the "
                         "specified duration: %s" % (sleep_time))
            time.sleep(float(sleep_time))
            # Set the cerberus status by checking the status of the
            # watched components/resources for the http server to publish it
            if watch_nodes_status and watch_etcd_status \
                and watch_openshift_apiserver_status \
                and watch_kube_apiserver_status \
                and watch_monitoring_stack_status \
                and watch_kube_controller_status \
                and watch_machine_api_status \
                and watch_openshift_ingress_status \
                and watch_kube_scheduler_status \
                and watch_openshift_sdn_status \
                and watch_ovnkubernetes_status:
                cerberus_status = True
            else:
                cerberus_status = False
                print("+{}Failed Components{}+".format("-" * (50), "-" * (50)))
                if not watch_nodes_status:
                    logging.info("Failed nodes: %s\n"
                                 % (failed_nodes))
                if not watch_etcd_status:
                    logging.info("Failed etcd pods: %s\n"
                                 % (failed_etcd_pods))
                if not watch_openshift_apiserver_status:
                    logging.info("Failed openshift apiserver pods: %s\n"
                                 % (failed_ocp_apiserver_pods))
                if not watch_kube_apiserver:
                    logging.info("Failed kube apiserver pods: %s\n"
                                 % (failed_kube_apiserver_pods))
                if not watch_monitoring_stack_status:
                    logging.info("Failed monitoring stack components: %s\n"
                                 % (failed_monitoring_stack))
                if not watch_kube_controller_status:
                    logging.info("Failed kube controller pods: %s\n"
                                 % (failed_kube_controller_pods))
                if not watch_machine_api_status:
                    logging.info("Failed machine api components: %s\n"
                                 % (failed_machine_api_components))
                if not watch_openshift_ingress_status:
                    logging.info("Failed ingress components: %s\n"
                                 % (failed_ocp_ingress_pods))
                if not watch_kube_scheduler_status:
                    logging.info("Failed kube scheduler pods: %s\n"
                                 % (failed_kube_scheduler_pods))
                if not watch_openshift_sdn_status:
                    logging.info("Failed openshfit sdn components: %s\n"
                                 % (failed_ocp_sdn_pods))
                if not watch_ovnkubernetes_status:
                    logging.info("Failed ocnkubernetes components: %s\n"
                                 % (failed_ovnkubernetes_pods))

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
