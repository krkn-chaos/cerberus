# Example Report

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
2020-03-26 22:05:32,118 [INFO] HTTP requests served: 1
2020-03-26 22:05:32,118 [INFO] Sleeping for the specified duration: 5
+--------------------------------------------------Failed Components--------------------------------------------------+
2020-03-26 22:05:37,123 [INFO] Failed openshfit sdn components: ['sdn-xmqhd']

2020-05-23 23:26:43,041 [INFO] ------------------------- Iteration Stats ---------------------------------------------
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_nodes in iteration 1: 0.0996248722076416 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_cluster_operators in iteration 1: 0.3672499656677246 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run watch_namespaces in iteration 1: 1.085144281387329 seconds
2020-05-23 23:26:43,041 [INFO] Time taken to run entire_iteration in iteration 1: 4.107403039932251 seconds
2020-05-23 23:26:43,041 [INFO] ---------------------------------------------------------------------------------------
```
