# Cerberus watchdog Guide

## Table of Contents
- [Cerberus watchdog Guide](#cerberus-watchdog-guide)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Tooling](#tooling)
  - [Workflow](#workflow)

## Introduction

One keypoint of a chaos infrastructure test is the way to obtain a reliable status of the health of your targeted cluster.
Cerberus is that master piece component that observe regulary various central components of your targeted cluster and return an updated
signal of the global health of you cluster.

For more detail about chaos challenges, read the [cerberus introduction to chaos testing](https://github.com/chaos-kubox/krkn/blob/main/docs/index.md#introduction)

## Tooling

In this section, we will go through how [cerberus](https://github.com/chaos-kubox/cerberus) - a cluster watchdog can help test the global health state of OpenShift and make sure you track state change and return an updated global health signal.

## Workflow

Let us start by understanding the workflow of Cerberus: the user will start by running cerberus by pointing to a specific OpenShift cluster using kubeconfig to be able to talk to the platform on top of which the OpenShift cluster is hosted. This can be done by either the oc/kubectl API or the cloud API. Based on the configuration of cerberus, it will [watch for nodes](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-nodes), 
[watch for cluster operators](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-cluster-operators), 
[watch for master schedulable status](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-master-schedulable-status), 
[watch for defined namespaces](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-namespaces) and
[watch for defined routes](https://github.com/startxfr/cerberus/blob/main/docs/config.md#watch-routes).
Accoridng to the result of theses check, cerberus will return a go/no-go signal representing the overall health of the cluster.

![Cerberus workflow](../media/cerberus-workflow.png)
