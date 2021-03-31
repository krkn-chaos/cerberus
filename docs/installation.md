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
$ docker pull quay.io/openshift-scale/cerberus
# Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).
$ docker run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml -d quay.io/openshift-scale/cerberus:latest
$ docker logs -f cerberus
```

Similarly, podman can be used to achieve the same:
```
$ podman pull quay.io/openshift-scale/cerberus
# Setup the [config](https://github.com/openshift-scale/cerberus/tree/master/config) according to your requirements. Information on the available options can be found at [usage](usage.md).
$ podman run --name=cerberus --net=host -v <path_to_kubeconfig>:/root/.kube/config:Z -v <path_to_cerberus_config>:/root/cerberus/config/config.yaml:Z -d quay.io/openshift-scale/cerberus:latest
$ podman logs -f cerberus
```

The go/no-go signal ( True or False ) gets published at http://`<hostname>`:8080. Note that the cerberus will only support ipv4 for the time being.

**NOTE**: The report is generated at /root/cerberus/cerberus.report inside the container, it can mounted to a directory on the host in case we want to capture it.

If you want to build your own Cerberus image, see [here](https://github.com/cloud-bulldozer/cerberus/tree/master/containers/build_own_image-README.md).
To run Cerberus on Power (ppc64le) architecture, build and run a containerized version by following the instructions given [here](https://github.com/cloud-bulldozer/cerberus/tree/master/containers/build_own_image-README.md).

## Run containerized Cerberus as a Kubernetes/OpenShift deployment
Refer to the [instructions](https://github.com/openshift-scale/cerberus/blob/master/containers/README.md#cerberus-as-a-kubernetesopenshift-application) for information on how to run cerberus as a Kubernetes or OpenShift application.
