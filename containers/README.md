### Cerberus image

Container image gets automatically built by quay.io at [Cerberus image](https://quay.io/repository/openshift-scale/cerberus). The builds will be triggered by any commit pushed to this repository.

### Run containerized version
Refer to the [instructions](https://github.com/cloud-bulldozer/cerberus/tree/master/containers/build_own_image-README.md) for information on how to build and run the containerized version of cerberus.

### Cerberus as a Kubernetes/OpenShift application
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
