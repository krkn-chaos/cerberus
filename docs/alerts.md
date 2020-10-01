# Alerts

Cerberus consumes the metrics from Prometheus deployed on the cluster to report the alerts. 

When provided the prometheus url and bearer token in the config, Cerberus reports the following alerts:

- KubeAPILatencyHigh: alerts at the end of each iteration and warns if 99th percentile latency for given requests to the kube-apiserver is above 1 second. It is the official SLI/SLO defined for Kubernetes.

- High number of etcd leader changes: alerts the user when an increase in etcd leader changes are observed on the cluster. Frequent elections may be a sign of insufficient resources, high network latency, or disruptions by other components and should be investigated.

**NOTE**: The prometheus url and bearer token are automatically picked from the cluster if the distribution is OpenShift since it's the default metrics solution. In case of Kubernetes, they need to be provided in the config if prometheus is deployed.

