## Cerberus watchdog Guide


### Table of Contents
- [Cerberus watchdog Guide](#cerberus-watchdog-guide)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Tooling](#tooling)
    - [Workflow](#workflow)
  - [Using Cerberus as part of a tekton pipeline](#using-cerberus-as-part-of-a-tekton-pipeline)
    - [Start as a single taskrun](#start-as-a-single-taskrun)
    - [Start as a pipelinerun](#start-as-a-pipelinerun)


### Introduction

One keypoint of a chaos infrastructure test is the way to obtain a reliable status of the health of your targeted cluster.
Cerberus is that master piece component that observe regulary various central components of your targeted cluster and return an updated
signal of the global health of you cluster.

For more detail about chaos challenges, read the [cerberus introduction to chaos testing](https://github.com/chaos-kubox/krkn/blob/main/docs/index.md#introduction)

### Tooling

In this section, we will go through how [cerberus](https://github.com/chaos-kubox/cerberus) - a cluster watchdog can help test the global health state of OpenShift and make sure you track state change and return an updated global health signal.

#### Workflow
Let us start by understanding the workflow of Cerberus: the user will start by running cerberus by pointing to a specific OpenShift cluster using kubeconfig to be able to talk to the platform on top of which the OpenShift cluster is hosted. This can be done by either the oc/kubectl API or the cloud API. Based on the configuration of cerberus, it will [watch for nodes](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-nodes), 
[watch for cluster operators](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-cluster-operators), 
[watch for master schedulable status](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-master-schedulable-status), 
[watch for defined namespaces](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-namespaces) and
[watch for defined routes](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-routes).
Accoridng to the result of theses check, cerberus will return a go/no-go signal representing the overall health of the cluster.

![Cerberus workflow](../media/cerberus-workflow.png)

### Using Cerberus as part of a tekton pipeline

You can find on [artifacthub.io](https://artifacthub.io/packages/search?kind=7&ts_query_web=cerberus) the 
[cerberus-check](https://artifacthub.io/packages/tekton-task/startx-tekton-catalog/cerberus-check) `tekton-task`
which can be used to check a cerberus signal (and a cluster global health) as part of a chaos pipeline.

To use this task, you must have **Openshift pipeline** enabled (or tekton CRD loaded for Kubernetes clusters)

#### Start as a single taskrun

```bash
oc project default
oc apply -f https://github.com/startxfr/tekton-catalog/raw/stable/task/cerberus-check/0.1/samples/taskrun.yaml
```

#### Start as a pipelinerun

```yaml
oc apply -f https://github.com/startxfr/tekton-catalog/raw/stable/task/cerberus-check/0.1/samples/pipelinerun.yaml
```