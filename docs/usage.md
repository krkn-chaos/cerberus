# Usage

### Config
Set the supported components to monitor and the tunings like number of iterations to monitor and duration to wait between each check in the config file located at config/config.yaml. A sample config looks like:

```
cerberus:
    distribution: openshift                              # Distribution can be kubernetes or openshift
    kubeconfig_path: ~/.kube/config                      # Path to kubeconfig
    port: 8080                                           # http server port where cerberus status is published
    watch_nodes: True                                    # Set to True for the cerberus to monitor the cluster nodes
    watch_cluster_operators: True                        # Set to True for cerberus to monitor cluster operators. Parameter is optional, will set to True if not specified
    watch_url_routes:                                    # Route url's you want to monitor
        - - https://...
          - Bearer ****                                  # This parameter is optional, specify authorization need for get call to route
        - - http://...
    watch_namespaces:                                    # List of namespaces to be monitored
        -    openshift-etcd
        -    openshift-apiserver
        -    openshift-kube-apiserver
        -    openshift-monitoring
        -    openshift-kube-controller-manager
        -    openshift-machine-api
        -    openshift-kube-scheduler
        -    openshift-ingress
        -    openshift-sdn
    cerberus_publish_status: True                        # When enabled, cerberus starts a light weight http server and publishes the status
    inspect_components: False                            # Enable it only when OpenShift client is supported to run.
                                                         # When enabled, cerberus collects logs, events and metrics of failed components

    prometheus_url:                                      # The prometheus url/route is automatically obtained in case of OpenShift, please set it when the distribution is Kubernetes.
    prometheus_bearer_token:                             # The bearer token is automatically obtained in case of OpenShift, please set it when the distribution is Kubernetes. This is needed to authenticate with prometheus.
                                                         # This enables Cerberus to query prometheus and alert on observing high Kube API Server latencies.   

    slack_integration: False                             # When enabled, cerberus reports status of failed iterations in the slack channel
                                                         # The following env vars need to be set: SLACK_API_TOKEN ( Bot User OAuth Access Token ) and SLACK_CHANNEL ( channel to send notifications in case of failures )
                                                         # When slack_integration is enabled, a watcher can be assigned for each day. The watcher of the day is tagged while reporting failures in the slack channel. Values are slack member ID's.
    watcher_slack_ID:                                        # (NOTE: Defining the watcher id's is optional and when the watcher slack id's are not defined, the slack_team_alias tag is used if it is set else no tag is used while reporting failures in the slack channel.)
        Monday:
        Tuesday:
        Wednesday:
        Thursday:
        Friday:
        Saturday:
        Sunday:
    slack_team_alias:                                    # The slack team alias to be tagged while reporting failures in the slack channel when no watcher is assigned

    custom_checks:                                       # Relative paths of files conataining additional user defined checks
        -   custom_checks/custom_check_sample.py
        -   custom_check.py

tunings:
    iterations: 5                                        # Iterations to loop before stopping the watch, it will be replaced with infinity when the daemon mode is enabled
    sleep_time: 60                                       # Sleep duration between each iteration
    kube_api_request_chunk_size: 250                     # Large requests will be broken into the specified chunk size to reduce the load on API server and improve responsiveness.
    daemon_mode: True                                    # Iterations are set to infinity which means that the cerberus will monitor the resources forever
    cores_usage_percentage: 0.5                          # Set the fraction of cores to be used for multiprocessing

database:
    database_path: /tmp/cerberus.db                      # Path where cerberus database needs to be stored
    reuse_database: False                                # When enabled, the database is reused to store the failures
```
**NOTE**: watch_namespaces support regex patterns. Any valid regex pattern can be used to watch all the namespaces matching the regex pattern. For example, `^openshift-.*$` can be used to watch all namespaces that start with `openshift-` or `openshift` can be used to watch all namespaces that have `openshift` in it.

**NOTE**: The current implementation can monitor only one cluster from one host. It can be used to monitor multiple clusters provided multiple instances of Cerberus are launched on different hosts.

**NOTE**: The components especially the namespaces needs to be changed depending on the distribution i.e Kubernetes or OpenShift. The default specified in the config assumes that the distribution is OpenShift. A config file for Kubernetes is located at config/kubernetes_config.yaml
