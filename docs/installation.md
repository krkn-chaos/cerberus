## Installation

Following ways are supported to run Cerberus:

- Standalone python program through Git or python package
- Containerized version using either Podman or Docker as the runtime
- Kubernetes or OpenShift deployment

**NOTE**: Only OpenShift 4.x versions are tested.


## Git
```
$ git clone https://github.com/openshift-scale/cerberus.git
```

### Install the dependencies
**NOTE**: Recommended to use a virtual environment(pyenv,venv) so as to prevent conflicts with already installed packages.
```
$ pip3 install -r requirements.txt
```

### Configure and Run
Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).

#### Run
```
$ python3 start_cerberus.py --config <config_file_location>
```

**NOTE**: When config file location is not passed, default [config](https://github.com/openshift-scale/cerberus/tree/master/config) is used.


## Python Package
Cerberus is also available as a python package to ease the installation and setup.

To install the lastest release:

```
$ pip3 install cerberus-client
```

### Configure and Run
Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).

#### Run
```
$ cerberus_client -c <config_file_location>`
```

**NOTE**: When config_file_location is not passed, default [config](https://github.com/openshift-scale/cerberus/tree/master/config) is used.
**NOTE**: It's recommended to run Cerberus either using the containerized  or github version to be able to use the latest enhancements and fixes.

## Containerized version

Assuming docker ( 17.05 or greater with multi-build support ) is intalled on the host, run:
```
$ docker pull quay.io/chaos-kubox/cerberus
# Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).
$ docker run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml -d quay.io/chaos-kubox/cerberus:latest
$ docker logs -f cerberus
```

Similarly, podman can be used to achieve the same:
```
$ podman pull quay.io/chaos-kubox/cerberus
# Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).
$ podman run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config:Z -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml:Z -d quay.io/chaos-kubox/cerberus:latest
$ podman logs -f cerberus
```

The go/no-go signal ( True or False ) gets published at http://`<hostname>`:8080. Note that the cerberus will only support ipv4 for the time being.

**NOTE**: The report is generated at /root/cerberus/cerberus.report inside the container, it can mounted to a directory on the host in case we want to capture it.

If you want to build your own Cerberus image, see [here](https://github.com/cloud-bulldozer/cerberus/tree/master/containers/build_own_image-README.md).
To run Cerberus on Power (ppc64le) architecture, build and run a containerized version by following the instructions given [here](https://github.com/cloud-bulldozer/cerberus/tree/master/containers/build_own_image-README.md).

## Run in Kubernetes/OpenShift

### Using a deployment

To run containerized Cerberus as a Kubernetes/OpenShift Deployment, follow these steps:
1. Configure the [config.yaml](https://github.com/openshift-scale/cerberus/tree/master/config) file according to your requirements.
2. Create a namespace under which you want to run the cerberus pod using `kubectl create ns <namespace>`.
3. Switch to `<namespace>` namespace:
    - In Kubernetes, use `kubectl config set-context --current --namespace=<namespace>`
    - In OpenShift, use `oc project <namespace>`
4. Create a ConfigMap named kube-config using `kubectl create configmap kube-config --from-file=<path_to_kubeconfig>`
5. Create a ConfigMap named cerberus-config using `kubectl create configmap cerberus-config --from-file=<path_to_cerberus_config>`
6. Create a serviceaccount to run the cerberus pod with privileges using `kubectl create serviceaccount useroot`.
    - In Openshift, execute `oc adm policy add-scc-to-user privileged -z useroot`.
7. Create a Deployment and a NodePort Service using `kubectl apply -f cerberus.yml`
8. Accessing the go/no-go signal:
    - In Kubernetes, execute `kubectl port-forward --address 0.0.0.0 pod/<cerberus_pod_name> 8080:8080` and access the signal at `http://localhost:8080` and `http://<hostname>:8080`.
    - In Openshift, create a route based on service cerberus-service using `oc expose service cerberus-service`. List all the routes using `oc get routes`. Use HOST/PORT associated with cerberus-service to access the signal.

NOTE: It is not recommended to run Cerberus internal to the cluster as the pod which is running Cerberus might get disrupted.

### Using a helm-chart

You can find on [artifacthub.io](https://artifacthub.io/packages/search?kind=0&ts_query_web=cerberus) the 
[chaos-cerberus](https://artifacthub.io/packages/helm/startx/chaos-cerberus) `helm-chart`
which can be used to deploy a cerberus server.

Default configuration create the following resources :

  - 1 project named **chaos-cerberus**
  - 1 scc with privileged context for **cerberus** deployment
  - 1 configmap named **cerberus-config** with cerberus configuration
  - 1 configmap named **cerberus-kubeconfig** with kubeconfig of the targeted cluster
  - 2 networkpolicy to allow kraken and route to consume the signal
  - 1 deployment named **cerberus**
  - 1 service to the cerberus pods
  - 1 route to the cerberus service

```bash
# Install the startx helm repository
helm repo add startx https://startxfr.github.io/helm-repository/packages/
# Install the cerberus project
helm install --set project.enabled=true chaos-cerberus-project  startx/chaos-cerberus
# Deploy the cerberus instance
helm install \
--set cerberus.enabled=true \
--set cerberus.kraken_allowed=true \
--set cerberus.kraken_ns="chaos-kraken" \
--set cerberus.kubeconfig.token.server="https://api.mycluster:6443" \
--set cerberus.kubeconfig.token.token="sha256~XXXXXXXXXX_PUT_YOUR_TOKEN_HERE_XXXXXXXXXXXX" \
-n chaos-cerberus \
chaos-cerberus-instance startx/chaos-cerberus
```

Refer to the [chaos-cerberus chart manpage](https://artifacthub.io/packages/helm/startx/chaos-cerberus)
and especially the [cerberus configuration values](https://artifacthub.io/packages/helm/startx/chaos-cerberus#chaos-cerberus-values-dictionary) 
for details on how to configure this chart.

## Consuming the cerberus signal

You can find various example in the [consume signal page](./consume-signal.md).
