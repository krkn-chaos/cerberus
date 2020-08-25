# Cerberus
Guardian of Kubernetes and OpenShift Clusters

Cerberus watches the Kubernetes/OpenShift clusters for dead nodes, system component failures/health and exposes a go or no-go signal which can be consumed by other workload generators or applications in the cluster and act accordingly.

### Workflow
![Cerberus workflow](media/cerberus-workflow.png)


## Ways to install and use Cerberus

### 1.  Cerberus as a Python Package
Cerberus is avialable as a python package to ease the installation and setup.

#### Installation
To install the lastest release:

`pip3 install cerberus-client`

#### Usage
To start cerberus monitoring, execute:

`cerberus_client -c <config_file_location>`

**NOTE**: When config_file_location is not passed, default config file is used.

### 2. Git clone the Cerberus repository
```
$ git clone https://github.com/openshift-scale/cerberus.git
```

#### Install the dependencies
```
$ pip3 install -r requirements.txt
```

### Usage

#### Config
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
                                                         # When slack_integration is enabled, a cop can be assigned for each day. The cop of the day is tagged while reporting failures in the slack channel. Values are slack member ID's.
    cop_slack_ID:                                        # (NOTE: Defining the cop id's is optional and when the cop slack id's are not defined, the slack_team_alias tag is used if it is set else no tag is used while reporting failures in the slack channel.)
        Monday:
        Tuesday:
        Wednesday:
        Thursday:
        Friday:
        Saturday:
        Sunday:
    slack_team_alias:                                    # The slack team alias to be tagged while reporting failures in the slack channel when no cop is assigned

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

#### Run
```
$ python3 start_cerberus.py --config <config_file_location>
```

#### Run containerized version
Assuming that the latest docker ( 17.05 or greater with multi-build support ) is intalled on the host, run:
```
$ docker pull quay.io/openshift-scale/cerberus
$ docker run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml -d quay.io/openshift-scale/cerberus:latest
$ docker logs -f cerberus
```

Similarly, podman can be used to achieve the same:
```
$ podman pull quay.io/openshift-scale/cerberus
$ podman run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config:Z -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml:Z -d quay.io/openshift-scale/cerberus:latest
$ podman logs -f cerberus
```
The go/no-go signal ( True or False ) gets published at http://`<hostname>`:8080. Note that the cerberus will only support ipv4 for the time being.

**NOTE**: The report is generated at /root/cerberus/cerberus.report inside the container, it can mounted to a directory on the host in case we want to capture it.

#### Run containerized Cerberus as a Kubernetes/OpenShift deployment
Refer to the [instructions](https://github.com/openshift-scale/cerberus/blob/master/containers/README.md#cerberus-as-a-kubeapp) for information on how to run cerberus as a KubeApp.

#### Report
The report is generated in the run directory and it contains the information about each check/monitored component status per iteration with timestamps. It also displays information about the components in case of failure. For example:

```
2020-03-26 22:05:06,393 [INFO] Starting ceberus
2020-03-26 22:05:06,401 [INFO] Initializing client to talk to the Kubernetes cluster
2020-03-26 22:05:06,434 [INFO] Fetching cluster info
2020-03-26 22:05:06,739 [INFO] Publishing cerberus status at http://0.0.0.0:8080
2020-03-26 22:05:06,753 [INFO] Starting http server at http://0.0.0.0:8080
2020-03-26 22:05:06,753 [INFO] Daemon mode enabled, cerberus will monitor forever
2020-03-26 22:05:06,753 [INFO] Ignoring the iterations set

2020-03-26 22:05:25,104 [INFO] Iteration 4: Node status: True
2020-03-26 22:05:25,133 [INFO] Iteration 4: Etcd member pods status: True
2020-03-26 22:05:25,161 [INFO] Iteration 4: OpenShift apiserver status: True
2020-03-26 22:05:25,546 [INFO] Iteration 4: Kube ApiServer status: True
2020-03-26 22:05:25,717 [INFO] Iteration 4: Monitoring stack status: True
2020-03-26 22:05:25,720 [INFO] Iteration 4: Kube controller status: True
2020-03-26 22:05:25,746 [INFO] Iteration 4: Machine API components status: True
2020-03-26 22:05:25,945 [INFO] Iteration 4: Kube scheduler status: True
2020-03-26 22:05:25,963 [INFO] Iteration 4: OpenShift ingress status: True
2020-03-26 22:05:26,077 [INFO] Iteration 4: OpenShift SDN status: True
2020-03-26 22:05:26,077 [INFO] HTTP requests served: 0 
2020-03-26 22:05:26,077 [INFO] Sleeping for the specified duration: 5


2020-03-26 22:05:31,134 [INFO] Iteration 5: Node status: True
2020-03-26 22:05:31,162 [INFO] Iteration 5: Etcd member pods status: True
2020-03-26 22:05:31,190 [INFO] Iteration 5: OpenShift apiserver status: True
127.0.0.1 - - [26/Mar/2020 22:05:31] "GET / HTTP/1.1" 200 -
2020-03-26 22:05:31,588 [INFO] Iteration 5: Kube ApiServer status: True
2020-03-26 22:05:31,759 [INFO] Iteration 5: Monitoring stack status: True
2020-03-26 22:05:31,763 [INFO] Iteration 5: Kube controller status: True
2020-03-26 22:05:31,788 [INFO] Iteration 5: Machine API components status: True
2020-03-26 22:05:31,989 [INFO] Iteration 5: Kube scheduler status: True
2020-03-26 22:05:32,007 [INFO] Iteration 5: OpenShift ingress status: True
2020-03-26 22:05:32,118 [INFO] Iteration 5: OpenShift SDN status: False
2020-03-26 22:05:32,118 [INFO] HTTP requests served: 1 
2020-03-26 22:05:32,118 [INFO] Sleeping for the specified duration: 5
+--------------------------------------------------Failed Components--------------------------------------------------+
2020-03-26 22:05:37,123 [INFO] Failed openshfit sdn components: ['sdn-xmqhd']

2020-05-23 23:26:43,041 [INFO] ------------------------- Iteration Stats ---------------------------------------------
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_nodes in iteration 1: 0.0996248722076416 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_cluster_operators in iteration 1: 0.3672499656677246 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_namespaces in iteration 1: 1.085144281387329 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run entire_iteration in iteration 1: 4.107403039932251 seconds
2020-05-23 23:26:43,041 [INFO] ---------------------------------------------------------------------------------------
```

#### Slack integration
The user has the option to enable/disable the slack integration ( disabled by default ). To use the slack integration, the user has to first create an [app](https://api.slack.com/apps?new_granular_bot_app=1) and add a bot to it on slack. SLACK_API_TOKEN and SLACK_CHANNEL environment variables have to be set. SLACK_API_TOKEN refers to Bot User OAuth Access Token and SLACK_CHANNEL refers to the slack channel ID the user wishes to receive the notifications.
- Reports when cerberus starts monitoring a cluster in the specified slack channel.
- Reports the component failures in the slack channel.
- A cop can be assigned for each day of the week. The cop of the day is tagged while reporting failures in the slack channel instead of everyone. (NOTE: Defining the cop id's is optional and when the cop slack id's are not defined, the slack_team_alias tag is used if it is set else no tag is used while reporting failures in the slack channel.)

#### Go or no-go signal
When the cerberus is configured to run in the daemon mode, it will continuosly monitor the components specified, runs a simple http server at http://0.0.0.0:8080 and publishes the signal i.e True or False depending on the components status. The tools can consume the signal and act accordingly.

#### Failures in a time window
1. The failures in the past 1 hour can be retrieved in the json format by visiting http://0.0.0.0:8080/history.
2. The failures in a specific time window can be retrieved in the json format by visiting http://0.0.0.0:8080/history?loopback=<interval>.
3. The failures between two time timestamps, the failures of specific issues types and the failures related to specific components can be retrieved in the json format by visiting http://0.0.0.0:8080/analyze url. The filters have to be applied to scrape the failures accordingly.

#### Node Problem Detector
[node-problem-detector](https://github.com/kubernetes/node-problem-detector) aims to make various node problems visible to the upstream layers in cluster management stack.

##### Installation
Please follow the instructions in the [installation](https://github.com/kubernetes/node-problem-detector#installation) section to setup Node Problem Detector on Kubernetes. The following instructions are setting it up on OpenShift:

1. Create `openshift-node-problem-detector` namespace [ns.yaml](https://github.com/openshift/node-problem-detector-operator/blob/master/deploy/ns.yaml) with        `oc create -f ns.yaml`
2. Add cluster role with `oc adm policy add-cluster-role-to-user system:node-problem-detector -z default -n openshift-node-problem-detector`
3. Add security context constraints with `oc adm policy add-scc-to-user privileged system:serviceaccount:openshift-node-problem-detector:default
`
4. Edit [node-problem-detector.yaml](https://github.com/kubernetes/node-problem-detector/blob/master/deployment/node-problem-detector.yaml) to fit your environment.
5. Edit [node-problem-detector-config.yaml](https://github.com/kubernetes/node-problem-detector/blob/master/deployment/node-problem-detector-config.yaml) to configure node-problem-detector.
6. Create the ConfigMap with	`oc create -f node-problem-detector-config.yaml`
7. Create the DaemonSet with `oc create -f node-problem-detector.yaml`

Once installed you will see node-problem-detector pods in openshift-node-problem-detector namespace. 
Now enable openshift-node-problem-detector in the [config.yaml](https://github.com/openshift-scale/cerberus/blob/master/config/config.yaml).
Cerberus just monitors `KernelDeadlock` condition provided by the node problem detector as it is system critical and can hinder node performance.

#### Custom checks
You can bring in additional checks to monitor components that are not being monitored by Cerberus. This can be accomplished by placing relative paths of files containing additional checks under custom_checks in config file. All the checks should be placed within the main function of the file. If the additional checks need to be considered in determining the go/no-go signal of Cerberus, the main function can return a boolean value for the same. However, it's optional to return a value. Refer to [example_check](https://github.com/openshift-scale/cerberus/blob/master/custom_checks/custom_check_sample.py) for an example custom check file.

#### Alerts
Monitoring metrics and alerting on abnormal behavior is critical as they are the indicators for clusters health. When provided the prometheus url and bearer token in the config, Cerberus looks for KubeAPILatencyHigh alert at the end of each iteration and warns if 99th percentile latency for given requests to the kube-apiserver is above 1 second. It is the official SLI/SLO defined for Kubernetes.

**NOTE**: The prometheus url and bearer token are automatically picked from the cluster if the distibution is OpenShift since it's the default metrics solution. In case of Kubernetes, they need to be provided in the config if prometheus is deployed.

### Use cases
There can be number of use cases, here are some of them:
- We run tools to push the limits of Kubernetes/OpenShift to look at the performance and scalability. There are a number of instances where system components or nodes start to degrade, which invalidates the results and the workload generator continues to push the cluster until it is unrecoverable.

- When running chaos experiments on a kubernetes/OpenShift cluster, they can potentially break the components unrelated to the targeted components which means that the choas experiment won't be able to find it. The go/no-go signal can be used here to decide whether the cluster recovered from the failure injection as well as to decide whether to continue with the next chaos scenario.

### What Kubernetes/OpenShift components can Cerberus monitor?
Following are the components of Kubernetes/OpenShift that Cerberus can monitor today, we will be adding more soon.

Component                | Description                                                                                                 | Working
------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------- |
Nodes                    | Watches all the nodes including masters, workers as well as nodes created using custom MachineSets          | :heavy_check_mark:        |
Namespaces               | Watches all the pods including containers running inside the pods in the namespaces specified in the config | :heavy_check_mark:        |
Cluster Operators        | Watches all Cluster Operators                                                                               | :heavy_check_mark:        |
Master Nodes Schedule    | Watches schedule of Master Nodes                                                                            | :heavy_check_mark:        |
Routes                   | Watches specified routes                                                                                    | :heavy_check_mark:        | 
CSRs                     | Warns if any CSRs are not approved                                                                         | :heavy_check_mark:        | 

**NOTE**: It supports monitoring pods in any namespaces specified in the config, the watch is enabled for system components mentioned in the [config](https://github.com/openshift-scale/cerberus/blob/master/config/config.yaml) by default as they are critical for running the operations on Kubernetes/OpenShift clusters.

### Blogs and other useful resources
- https://www.openshift.com/blog/openshift-scale-ci-part-4-introduction-to-cerberus-guardian-of-kubernetes/openshift-clouds
- https://www.openshift.com/blog/reinforcing-cerberus-guardian-of-openshift/kubernetes-clusters
