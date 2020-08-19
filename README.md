# Cerberus
Guardian of Kubernetes and OpenShift Clusters

Cerberus watches the Kubernetes/OpenShift clusters for dead nodes, system component failures/health and exposes a go or no-go signal which can be consumed by other workload generators or applications in the cluster and act accordingly.

### 1.  Cerberus as a Python Package
Cerberus is avialable as a python package to ease the installation and setup.

#### Installation
To install the lastest release:

`pip3 install cerberus-client`

#### Usage
To start cerberus monitoring, execute:

`cerberus_client -c <config_file_location>`

**NOTE**: When config_file_location is not passed, default config file is used.

Refer to [README](https://github.com/openshift-scale/cerberus/blob/master/README.md) for details on features offered by Cerberus and its usage.
