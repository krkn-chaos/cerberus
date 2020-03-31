# Cerberus
Guardian of Kubernetes Clusters

Cerberus watches the Kubernetes/OpenShift clusters for dead nodes, system component failures and exposes a go or no-go signal which can be consumed by other workload generators or applications in the cluster and act accordingly.

### Workflow
![Cerberus workflow](media/cerberus-workflow.png)

### Install the dependencies
```
$ pip3 install -r requirements.txt
```

### Usage

#### Config
Set the supported components to monitor and the tunings like number of iterations to monitor and duration to wait between each check in the config file located at config/config.yaml. A sample config looks like:

```
cerberus:
    kubeconfig_path: ~/.kube/config                      # Path to kubeconfig
    watch_nodes: True                                    # Set to True for the cerberus to monitor the cluster nodes
    watch_namespaces:                                    # List of namespaces to be monitored
        -    openshift-etcd
        -    openshift-apiserver
        -    openshift-kube-apiserver
        -    openshift-monitoring
        -    openshift-kube-controller
        -    openshift-machine-api
        -    openshift-kube-scheduler
        -    openshift-ingress
        -    openshift-sdn
        -    openshift-ovn-kubernetes
    cerberus_publish_status: True                        # When enabled, cerberus starts a light weight http server and publishes the status
    inspect_components: False                            # Enable it only when OpenShift client is supported to run.
                                                         # When enabled, cerberus collects logs, events and metrics of failed components
    slack_integration: False                             # When enabled, cerberus reports status of each iteration in slack channel

tunings:
    iterations: 5                                        # Iterations to loop before stopping the watch, it will be replaced with infinity when the daemon mode is enabled
    sleep_time: 60                                       # Sleep duration between each iteration
    daemon_mode: True                                    # Iterations are set to infinity which means that the cerberus will monitor the resources forever

```

#### Run
```
$ python3 start_cerberus.py --config <config_file_location>
```

#### Run containerized version
Assuming that the latest docker ( 17.05 or greater with multi-build support ) is intalled on the host, run:
```
$ cd containers
$ docker pull quay.io/openshift-scale/cerberus
$ docker run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml -d quay.io/openshift-scale/cerberus:latest
$ docker logs -f cerberus
```

Similarly, podman can be used to achieve the same:
```
$ cd containers
$ podman pull quay.io/openshift-scale/cerberus
$ podman run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config:Z -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml:Z -d quay.io/openshift-scale/cerberus:latest
$ podman logs -f cerberus
```
The go/no-go signal ( True or False ) gets published at http://<hostname>:8080. Note that the cerberus will only support ipv4 for the time being.

NOTE: The report is generated at /root/cerberus/cerberus.report inside the container, it can mounted to a directory on the host in case we want to capture it.

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
2020-03-26 22:05:26,077 [INFO] Cerberus is not monitoring openshift-ovn-kubernetes, assuming it's up and running
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
2020-03-26 22:05:32,118 [INFO] Cerberus is not monitoring openshift-ovn-kubernetes, assuming it's up and running 
2020-03-26 22:05:32,118 [INFO] HTTP requests served: 1 
2020-03-26 22:05:32,118 [INFO] Sleeping for the specified duration: 5
+--------------------------------------------------Failed Components--------------------------------------------------+
2020-03-26 22:05:37,123 [INFO] Failed openshfit sdn components: ['sdn-xmqhd']
```

#### Slack integration
The user has the option to enable/disable the slack integration. To use the slack integration, the user has to first create an [app](https://api.slack.com/apps?new_granular_bot_app=1) and add a bot to it on slack. Two env variables SLACK_API_TOKEN and SLACK_CHANNEL have to be set. SLACK_API_TOKEN refers to Bot User OAuth Access Token and SLACK_CHANNEL refers to the slack channel the user wishes to receive the notifications in. When enabled, cerberus reports the following on slack:
- Notifies the start of cerberus monitoring.
- Notifies the status of each iteration.
- Sends the cerberus report at the end of an iteration in case of a failure.
- Sends the cerberus report after completion of specified number of iterations set by the user.

#### Go or no-go signal
When the cerberus is configured to run in the daemon mode, it will continuosly monitor the components specified, runs a simple http server at http://0.0.0.0:8080 and publishes the signal i.e True or False depending on the components status. The tools can consume the signal and act accordingly.

#### Usecase
There can be number of usecases, here are some of them:
- We run tools to push the limits of Kubenetes/OpenShift to look at the performance and scalability and there are number of instances where the system components or nodes starts to degrade in which case the results are no longer valid but the workload generator continues to push the cluster till it breaks. The signal published by the Cerberus can be consumed by the workload generators to act on i.e stop the workload and notify us in this case.

- When running chaos experiments on a kubernetes/OpenShift cluster, they can potentially break the components unrelated to the targeted components which means that the choas experiment won't be able to find it. The go/no-go signal can be used here to decide whether the cluster recovered from the failure injection as well as to decide whether to continue with the next chaos scenario.

### Kubernetes/OpenShift components supported
Following are the components of Kubernetes/OpenShift that Cerberus can monitor today, we will be adding more soon.

Component                | Description                                                                                        | Working
------------------------ | ---------------------------------------------------------------------------------------------------| ------------------------- |
Nodes                    | Watches all the nodes including masters, workers as well as nodes created using custom MachineSets | :heavy_check_mark:        |
Etcd                     | Watches the status of the Etcd member pods                                                         | :heavy_check_mark:        |
OpenShift ApiServer      | Watches the OpenShift Apiserver pods                                                               | :heavy_check_mark:        |
Kube ApiServer           | Watches the Kube APiServer pods                                                                    | :heavy_check_mark:        |
Monitoring               | Watches the monitoring stack                                                                       | :heavy_check_mark:        |
Kube Controller          | Watches Kube controller                                                                            | :heavy_check_mark:        |
Machine API              | Watches machine controller, cluster auto-scaler, machine-api-operator                              | :heavy_check_mark:        |
Kube Scheduler           | Watches Kube scheduler                                                                             | :heavy_check_mark:        |
Ingress                  | Watches Routers                                                                                    | :heavy_check_mark:        |
Openshift SDN            | Watches SDN pods                                                                                   | :heavy_check_mark:        |
OVNKubernetes            | Watches OVN pods                                                                                   | :heavy_check_mark:        |
