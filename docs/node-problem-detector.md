# Node Problem Detector
[node-problem-detector](https://github.com/kubernetes/node-problem-detector) aims to make various node problems visible to the upstream layers in cluster management stack.

### Installation
Please follow the instructions in the [installation](https://github.com/kubernetes/node-problem-detector#installation) section to setup Node Problem Detector on Kubernetes. The following instructions are setting it up on OpenShift:

1. Create `openshift-node-problem-detector` namespace [ns.yaml](https://github.com/openshift/node-problem-detector-operator/blob/master/deploy/ns.yaml) with        `oc create -f ns.yaml`
2. Add cluster role with `oc adm policy add-cluster-role-to-user system:node-problem-detector -z default -n openshift-node-problem-detector`
3. Add security context constraints with `oc adm policy add-scc-to-user privileged system:serviceaccount:openshift-node-problem-detector:default
`
4. Edit [node-problem-detector.yaml](https://github.com/kubernetes/node-problem-detector/blob/master/deployment/node-problem-detector.yaml) to fit your environment.
5. Edit [node-problem-detector-config.yaml](https://github.com/kubernetes/node-problem-detector/blob/master/deployment/node-problem-detector-config.yaml) to configure node-problem-detector.
6. Create the ConfigMap with    `oc create -f node-problem-detector-config.yaml`
7. Create the DaemonSet with `oc create -f node-problem-detector.yaml`

Once installed you will see node-problem-detector pods in openshift-node-problem-detector namespace.
Now enable openshift-node-problem-detector in the [config.yaml](https://github.com/openshift-scale/cerberus/blob/master/config/config.yaml).
Cerberus just monitors `KernelDeadlock` condition provided by the node problem detector as it is system critical and can hinder node performance.

