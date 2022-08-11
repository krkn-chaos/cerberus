Cerberus Config Components Explained

* [Sample Config](#config)
* [Watch Nodes](#watch-nodes)
* [Watch Operators](#watch-cluster-operators)
* [Watch Routes](#watch-routes)
* [Watch Master Schedulable Status](#watch-master-schedulable-status)
* [Watch Namespaces](#watch-namespaces)
* [Watch Terminating Namespaces](#watch-terminating-namespaces)
* [Publish Status](#publish-status)
* [Inpsect Components](#inspect-components)
* [Custom Checks](#custom-checks)

### Config
Set the components to monitor and the tunings like duration to wait between each check in the config file located at config/config.yaml. A sample config looks like:

```
cerberus:
    distribution: openshift                              # Distribution can be kubernetes or openshift
    kubeconfig_path: /root/.kube/config                      # Path to kubeconfig
    port: 8081                                           # http server port where cerberus status is published
    watch_nodes: True                                    # Set to True for the cerberus to monitor the cluster nodes
    watch_cluster_operators: True                        # Set to True for cerberus to monitor cluster operators
    watch_terminating_namespaces: True                   # Set to True to monitor if any namespaces (set below under 'watch_namespaces' start terminating
    watch_url_routes:
    # Route url's you want to monitor, this is a double array with the url and optional authorization parameter
    watch_master_schedulable:                            # When enabled checks for the schedulable master nodes with given label.
        enabled: True
        label: node-role.kubernetes.io/master
    watch_namespaces:                                    # List of namespaces to be monitored
        -    openshift-etcd
        -    openshift-apiserver
        -    openshift-kube-apiserver
        -    openshift-monitoring
        -    openshift-kube-controller-manager
        -    openshift-machine-api
        -    openshift-kube-scheduler
        -    openshift-ingress
        -    openshift-sdn                                   # When enabled, it will check for the cluster sdn and monitor that namespace
    watch_namespaces_ignore_pattern: []                  # Ignores pods matching the regex pattern in the namespaces specified under watch_namespaces
    cerberus_publish_status: True                        # When enabled, cerberus starts a light weight http server and publishes the status
    inspect_components: False                            # Enable it only when OpenShift client is supported to run
                                                         # When enabled, cerberus collects logs, events and metrics of failed components

    prometheus_url:                                      # The prometheus url/route is automatically obtained in case of OpenShift, please set it when the distribution is Kubernetes.
    prometheus_bearer_token:                             # The bearer token is automatically obtained in case of OpenShift, please set it when the distribution is Kubernetes. This is needed to authenticate with prometheus.
                                                         # This enables Cerberus to query prometheus and alert on observing high Kube API Server latencies.

    slack_integration: False                             # When enabled, cerberus reports the failed iterations in the slack channel
                                                         # The following env vars needs to be set: SLACK_API_TOKEN ( Bot User OAuth Access Token ) and SLACK_CHANNEL ( channel to send notifications in case of failures )
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

    custom_checks:
        -   custom_checks/custom_check_sample.py       # Relative paths of files conataining additional user defined checks

tunings:
    timeout: 20                                          # Number of seconds before requests fail
    iterations: 1                                        # Iterations to loop before stopping the watch, it will be replaced with infinity when the daemon mode is enabled
    sleep_time: 3                                       # Sleep duration between each iteration
    kube_api_request_chunk_size: 250                     # Large requests will be broken into the specified chunk size to reduce the load on API server and improve responsiveness.
    daemon_mode: True                                    # Iterations are set to infinity which means that the cerberus will monitor the resources forever
    cores_usage_percentage: 0.5                          # Set the fraction of cores to be used for multiprocessing

database:
    database_path: /tmp/cerberus.db                      # Path where cerberus database needs to be stored
    reuse_database: False                                # When enabled, the database is reused to store the failures
```

#### Watch Nodes
This flag returns any nodes where the KernelDeadlock is not set to False and does not have a `Ready` status

#### Watch Cluster Operators
When `watch_cluster_operators` is set to True, this will monitor the degraded status of all the cluster operators and report a failure if any are degraded.
If set to False will not query or report the status of the cluster operators


#### Watch Routes
This parameter expects a double array with each item having the url and an optional bearer token or authorization for each of the url's to properly connect

For example:
```
watch_url_routes:
- - <url>
  - <authorization> (optional)
- - https://prometheus-k8s-openshift-monitoring.apps.****.devcluster.openshift.com
  - Bearer ****
- - http://nodejs-mongodb-example-default.apps.****.devcluster.openshift.com

```

#### Watch Master Schedulable Status
When this check is enabled, cerberus queries each of the nodes for the given label and verifies the taint effect does not equal "NoSchedule"
```
watch_master_schedulable:                            # When enabled checks for the schedulable master nodes with given label.
    enabled: True
    label: <label of master nodes>
```


#### Watch Namespaces
It supports monitoring pods in any namespaces specified in the config, the watch is enabled for system components mentioned in the [config](https://github.com/openshift-scale/cerberus/blob/master/config/config.yaml) by default as they are critical for running the operations on Kubernetes/OpenShift clusters.

`watch_namespaces` support regex patterns. Any valid regex pattern can be used to watch all the namespaces matching the regex pattern.
For example, `^openshift-.*$` can be used to watch all namespaces that start with `openshift-` or `openshift` can be used to watch all namespaces that have `openshift` in it.
Or you can use `^.*$` to watch all namespaces in your cluster


#### Watch Terminating Namespaces
When `watch_terminating_namespaces` is set to True, this will monitor the status of all the namespaces defind under watch namespaces and report a failure if any are terminating.
If set to False will not query or report the status of the terminating namespaces

#### Publish Status
Parameter to set if you want to publish the go/no-go signal to the http server


#### Inspect Components
`inspect_components` if set to True will perform an `oc adm inspect namespace <namespace>` when any namespace has any failing pods


#### Custom Checks
Users can add additional checks to monitor components that are not being monitored by Cerberus and consume it as part of the go/no-go signal.  This can be accomplished by placing relative paths of files containing additional checks under custom_checks in config file. All the checks should be placed within the main function of the file. If the additional checks need to be considered in determining the go/no-go signal of Cerberus, the main function can return a boolean value for the same. Having a dict return value of the format {'status':status, 'message':message} shall send signal to Cerberus along with message to be displayed in slack notification. However, it's optional to return a value.

Refer to [example_check](https://github.com/openshift-scale/cerberus/blob/master/custom_checks/custom_check_sample.py) for an example custom check file.
