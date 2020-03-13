# Cerberus
Guardian of Kubernetes Clusters

Cerberus watches the Kubernetes/OpenShift clusters for dead nodes, system component failures and exposes a go or no-go signal which can be consumed by other workload generators or applications in the cluster and act accordingly.

### Install the dependencies
```
$ pip3 install -r requirements.txt
```

### Usage

#### Config
Set the supported components to monitor and the tunings like number of iterations to monitor and duration to wait between each check in the config file. A sample config looks like:

```
[cerberus]
# Set to True for the cerberus to monitor the cluster nodes
watch_nodes: True

# Set to True for the cerberus to monitor the etcd members
watch_etcd: True

# Namespace to look for the etcd member pods
etcd_namespace: openshift-etcd

# Set to True for the cerberus to monitor openshift-apiserver pods
watch_openshift_apiserver: True

# Namespace to look for the openshift-apiserver pods
openshift_apiserver_namespace: openshift-apiserver

# When enabled, cerberus starts a light weight http server and publishes the status
cerberus_publish_status: True

[tunings]
# Iterations to loop before stopping the watch, it will be replaced with infinity when the daemon mode is enabled
iterations: 5

# Sleep duration between each iteration
sleep_time: 30

# Iterations are set to infinity which means that the cerberus will monitor the resources forever
daemon_mode: True

```

#### Run
```
$ python3 cerberus.py --config <config_file_location>
```

#### Go or no-go signal
When the cerberus is configured to run in the daemon mode, it will continuosly monitor the components specified, runs a simple http server at http://localhost:8086 and publishes the signal i.e True or False depending on the components status. The tools can consume the signal and act accordingly. 

#### Usecase
There can be number of usecases, here is one of them:
We run tools to push the limits of Kubenetes/OpenShift to look at the performance and scalability and there are number of instances where the system components or nodes starts to degrade in which case the results are no longer valid but the workload generator continues to push the cluster till it breaks. The signal published by the Cerberus can be consumed by the workload generators to act on i.e stop the workload and notify us in this case.

### Kubernetes/OpenShift components supported
Following are the components of Kubernetes/OpenShift that Cerberus can monitor today, we will be adding more soon.

Component                | Description                                                                                        | Working
------------------------ | ---------------------------------------------------------------------------------------------------| ------------------------- |
Nodes                    | Watches all the nodes including masters, workers as well as nodes created using custom MachineSets | :heavy_check_mark:        |
Etcd                     | Watches the status of the Etcd member pods                                                         | :heavy_check_mark:        |
OpenShift ApiServer      | Watches the OpenShift Apiserver pods                                                               | :heavy_check_mark:        |
Kube ApiServer           | Watches the Kube APiServer pods                                                                    | In progress               |
