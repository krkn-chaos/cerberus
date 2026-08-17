# Alerts

Cerberus consumes the metrics from Prometheus deployed on the cluster to report the alerts.

When provided the prometheus url and bearer token in the config, Cerberus queries Prometheus for configured alerts each iteration.

## Included alerts

The default `kubernetes_config.yaml` includes the following alerts as a starting point:

- **KubeAPILatencyHigh**: warns if 99th percentile latency for given requests to the kube-apiserver is above 1 second. It is the official SLI/SLO defined for Kubernetes.

- **etcdHighNumberOfLeaderChanges**: warns when an increase in etcd leader changes are observed on the cluster. Frequent elections may be a sign of insufficient resources, high network latency, or disruptions by other components and should be investigated.

## Configuring alerts

You can configure which Prometheus alerts Cerberus monitors by setting the `prometheus_alerts` list in the config. Each entry supports:

- `expr` (required): Any valid PromQL expression. Can be a simple `ALERTS{}` selector or a complex metric query with functions, aggregations, and thresholds.
- `description`: The warning message logged when the expression returns results (default: the expression itself)
- `severity`: Severity level used in log output (default: `warning`)

This uses the same format as [krkn's alert config](https://github.com/krkn-chaos/krkn), so you can use arbitrary PromQL expressions — not just alert names.

Example config:

```yaml
cerberus:
    prometheus_alerts:
        # Check fired Prometheus alerts by name
        -   expr: ALERTS{alertname="KubeAPILatencyHigh", severity="warning"}
            description: "99th percentile kube-apiserver latency is above 1 second."
            severity: warning

        # Raw PromQL expression for etcd fsync latency
        -   expr: avg_over_time(histogram_quantile(0.99, rate(etcd_disk_wal_fsync_duration_seconds_bucket[2m]))[10m:]) > 0.01
            description: "10 min avg 99th etcd fsync latency higher than 10ms."
            severity: warning

        # etcd leader changes via raw metric
        -   expr: rate(etcd_server_leader_changes_seen_total[2m]) > 0
            description: "etcd leader changes observed."
            severity: warning

        # Control plane pod down
        -   expr: up{namespace=~"openshift-etcd"} == 0
            description: "etcd pod down."
            severity: warning

        # Catch all critical Prometheus alerts
        -   expr: ALERTS{severity="critical", alertstate="firing"} > 0
            description: "Critical prometheus alert firing."
            severity: critical
```

If `prometheus_alerts` is omitted from the config, no Prometheus alerts are monitored. The default `kubernetes_config.yaml` includes KubeAPILatencyHigh and etcdHighNumberOfLeaderChanges as a starting point.

**NOTE**: The prometheus url and bearer token are automatically picked from the cluster if the distribution is OpenShift since it's the default metrics solution. In case of Kubernetes, they need to be provided in the config if prometheus is deployed.
