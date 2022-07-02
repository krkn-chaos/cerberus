# Consume cerberus signal

Various examples on how to comsume the Cerberus signal :

- Using a simple http client (cURL)
- As an init container for a Pod
- As a tekton task (part of a pipeline)

## Simple check with curl

if you just want to check the cerberus signal, you can use this small script to check the cerberus signal.

```bash
export CERBERUS_URL=http://cerberus.chaos-cerberus.svc.cluster.local:8080
if curl -s "$CERBERUS_URL" | grep True &> /dev/null; then
    echo "Cerberus check is OK at ${CERBERUS_URL}"
else
    echo "Cerberus check is NOT OK at ${CERBERUS_URL}"
fi
```

## As an init container

This example allow you to start a container when cerberus return a OK signal.

```yaml
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cerberus-config-job
data:
  cerberus_url: "cerberus.default.svc.cluster.local" 
---
apiVersion: batch/v1
kind: Job
metadata:
  name: "check-node-if-cerberus-ok"
spec:
  template:
    spec:
      initContainers:
      - name: check-cerberus
        image: quay.io/startx/runner-oc:fc35
        command: ['bash', '-c', "until curl -s $CERBERUS_URL | grep True &> /dev/null; do echo Wait for OK from cerberus at $CERBERUS_URL; sleep 2; done"]
        env:
        - name: CERBERUS_URL
          valueFrom:
            configMapKeyRef:
              name: cerberus-config-job
              key: cerberus_url
      containers:
      - name: job-task
        image: "quay.io/startx/runner-oc:fc35"
        command:
          - "/bin/bash"
          - "-c"
          - |-
            echo "executed after a POSITIVE cerberus check agains't $CERBERUS_URL"
            echo "Replace this container definition with your own description"
            exit
        env:
        - name: CERBERUS_URL
          valueFrom:
            configMapKeyRef:
              name: cerberus-config-job
              key: cerberus_url
        resources:
          requests:
            cpu: "10m"
            memory: "64Mi"
          limits:
            cpu: "50m"
            memory: "128Mi"
      restartPolicy: Never
  backoffLimit: 2
```

## Using tekton pipeline

You can find on [artifacthub.io](https://artifacthub.io/packages/search?kind=7&ts_query_web=cerberus) the 
[cerberus-check](https://artifacthub.io/packages/tekton-task/startx-tekton-catalog/cerberus-check) `tekton-task`
which can be used to check a cerberus signal (and a cluster global health) as part of a chaos pipeline.
You can read [tekton concepts](https://tekton.dev/docs/concepts/overview/), [tekton pipeline entities](https://github.com/tektoncd/pipeline/blob/main/docs/README.md#tekton-pipelines-entities), [tekton getting started](https://tekton.dev/docs/getting-started/tasks/) and the 
[openshift pipeline documentation](https://docs.openshift.com/container-platform/4.10/cicd/pipelines/understanding-openshift-pipelines.html) 
to get familiar with this project.

### Installing tekton

#### OpenShift cluster

To use this task, you must have tekton enabled into your cluster. For Openshift cluster, an operator named **Openshift pipeline** enable tekton in your cluster. You can use the OperatorHub to find in in your openshift cluster. You can also use [startx helm-chart pipeline](https://helm-repository.readthedocs.io/en/latest/charts/cluster-pipeline/) for easy and automatic install.

#### Kubernetes cluster

```bash
kubectl apply --filename https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
kubectl get pods --namespace tekton-pipelines --watch
```

### Running cerberus tekton task

#### Start as a single taskrun

```bash
kubectl project default
kubectl apply -f https://github.com/startxfr/tekton-catalog/raw/stable/task/cerberus-check/0.1/samples/taskrun.yaml
kubectl get taskrun pod
```

#### Start as a pipelinerun

```yaml
kubectl project default
kubectl apply -f https://github.com/startxfr/tekton-catalog/raw/stable/task/cerberus-check/0.1/samples/pipelinerun.yaml
kubectl get pipelinerun taskrun pod
```